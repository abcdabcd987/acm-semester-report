import os
import uuid
import yaml
import json
import functools
import subprocess
from datetime import datetime
from flask import request, redirect, session, url_for, flash, render_template, jsonify, abort, send_file, Response
from acm_report import app
from acm_report.models import *
from acm_report.database import db_session
from acm_report.mail import send_vericode
import acm_report.settings as settings
import acm_report.utils as utils


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        verified = session.get('verified', None)
        if verified is None:
            flash('请登入', 'warning')
            return redirect(url_for('get_login'))
        elif not verified:
            flash('请验证', 'warning')
            return redirect(url_for('get_login_verify'))
        return f(*args, **kwargs)
    return decorated_function


@app.route(settings.WEBROOT + '/')
def get_homepage():
    forms = db_session.query(Form).order_by(Form.id.desc()).all()
    now = datetime.utcnow()
    active = set(form.id for form in forms if form.start_time < now < form.end_time)
    return render_template('homepage.html', forms=forms, active=active)


@app.route(settings.WEBROOT + '/login')
def get_login():
    return render_template('login.html')


@app.route(settings.WEBROOT + '/login', methods=['POST'])
def post_login():
    email = request.form.get('email', '')
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        flash('没有找到 %s 对应的用户' % email, 'warning')
        return redirect(url_for('get_login'))

    session.clear()
    session['sid'] = uuid.uuid4().hex
    session['user_id'] = user.id
    session['user_email'] = user.email
    session['user_year'] = user.year
    session['user_name'] = user.name
    session['user_stuid'] = user.stuid
    session['vericode'] = uuid.uuid4().hex
    session['verified'] = False
    err = send_vericode(user.email, 'ACM%d-%s' % (user.year, user.name), session['vericode'])
    if err:
        flash('发送邮件失败！<pre>%s</pre>' % err, 'warning')
        return redirect(url_for('get_login'))
    flash('验证码已发送至 <code>%s</code>' % email, 'success')
    return redirect(url_for('get_login_verify'))


@app.route(settings.WEBROOT + '/login/verify')
def get_login_verify():
    verified = session.get('verified', None)
    if verified:
        flash('已登入', 'success')
        return redirect(url_for('get_homepage'))
    elif verified is None or 'vericode' not in session:
        flash('请登入', 'warning')
        return redirect(url_for('get_login'))
    return render_template('login_verify.html')


@app.route(settings.WEBROOT + '/login/verify', methods=['POST'])
def post_login_verify():
    expected = session.get('vericode', None)
    verified = session.get('verified', None)
    if expected is None:
        flash('请登入', 'warning')
        return redirect(url_for('get_login'))
    if verified:
        flash('已登入', 'success')
        return redirect(url_for('get_homepage'))
    vericode = request.form.get('vericode', None)
    if vericode != expected:
        flash('验证码错误', 'warning')
        return redirect(url_for('get_login_verify'))
    session['verified'] = True
    del session['vericode']
    flash('登入成功', 'success')
    return redirect(url_for('get_homepage'))


@app.route(settings.WEBROOT + '/logout')
@login_required
def get_logout():
    session.clear()
    flash('登出成功', 'success')
    return redirect(url_for('get_homepage'))


@app.route(settings.WEBROOT + '/report/create/<int:form_id>')
@login_required
def get_report_create(form_id):
    form = db_session.query(Form).filter(Form.id == form_id).first()
    if not form:
        abort(404)
    config = yaml.load(form.config_yaml)
    if session['user_year'] not in config['students']:
        abort(404)

    latest_report = db_session.query(Report)\
                              .filter(Report.user_id == session['user_id'])\
                              .filter(Report.form_id == form_id)\
                              .order_by(Report.id.desc()).first()
    report = json.loads(latest_report.json) if latest_report else None

    return render_template('report_create.html', form=form, config=config, report=report)


@app.route(settings.WEBROOT + '/report/create/<int:form_id>', methods=['POST'])
@login_required
def post_report_create(form_id):
    form = db_session.query(Form).filter(Form.id == form_id).first()
    if not form:
        abort(404)
    config = yaml.load(form.config_yaml)
    if session['user_year'] not in config['students']:
        abort(404)

    content = {}
    for section in config['sections']:
        repeat = 'repeat' in section
        l = []
        for field in section['fields']:
            values = request.form.getlist(section['id'] + '.' + field['id'] + '[]')
            for _ in range(len(values) - len(l)):
                l.append({f['id']: '' for f in section['fields']})
            for i, value in enumerate(values):
                l[i][field['id']] = value.strip()
        content[section['id']] = l

    report = Report(user_id=session['user_id'],
                    form_id=form_id,
                    json=json.dumps(content),
                    created_at=datetime.utcnow())
    db_session.add(report)
    db_session.commit()
    flash('提交成功', 'success')
    return redirect(url_for('get_report', id=report.id))


@app.route(settings.WEBROOT + '/report/<int:id>')
@login_required
def get_report(id):
    report = db_session.query(Report).filter(Report.id == id).first()
    form = db_session.query(Form).filter(Form.id == report.form_id).first()
    if not report or report.user_id != session['user_id'] or not form:
        abort(404)

    config = yaml.load(form.config_yaml)
    report = json.loads(report.json)
    return render_template('report.html', config=config, report=report)


@app.route(settings.WEBROOT + '/form/<int:form_id>')
def get_form(form_id):
    form = db_session.query(Form).filter(Form.id == form_id).first()
    if not form:
        abort(404)
    reports = db_session.query(Report)\
                        .filter(Report.created_at.between(form.start_time, form.end_time))\
                        .filter(Report.form_id == form_id)\
                        .order_by(Report.id.desc())\
                        .all()
    my_reports = []
    last_report = {}
    user_id = session.get('user_id', None)
    for r in reports:
        last = last_report.get(r.user_id, None)
        if not last or last < r.created_at:
            last_report[r.user_id] = r.created_at
        if user_id and r.user_id == user_id:
            my_reports.append(r)

    config = yaml.load(form.config_yaml)
    users = { y: [] for y in config['students'] }
    for u in db_session.query(User).filter(User.year.in_(config['students'])).order_by(User.stuid.asc()).all():
        users[u.year].append(u)
    return render_template('form.html',
                           form=form,
                           config=config,
                           reports=last_report,
                           users=users,
                           my_reports=my_reports)


@app.route(settings.WEBROOT + '/form/<int:form_id>.yaml')
def get_form_yaml(form_id):
    form = db_session.query(Form).filter(Form.id == form_id).first()
    if not form:
        abort(404)
    return Response(form.config_yaml, mimetype='text/yaml')
