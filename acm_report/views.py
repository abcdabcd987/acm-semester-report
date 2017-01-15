# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import uuid
import json
import functools
import subprocess
from datetime import datetime
from flask import request, redirect, session, url_for, flash, render_template, jsonify, abort, send_file
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
    return render_template('homepage.html')


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


@app.route(settings.WEBROOT + '/report/create')
@login_required
def get_report_create():
    year, season = utils.date2semester(datetime.utcnow())
    if season == 'spring':
        date_st = datetime(year, 3, 1)
        date_ed = datetime(year, 10, 1)
    else:
        date_st = datetime(year, 10, 1)
        date_ed = datetime(year+1, 3, 1)

    report = db_session.query(Report)\
                       .filter(Report.user_id == session['user_id'])\
                       .filter(Report.created_at >= date_st)\
                       .filter(Report.created_at < date_ed)\
                       .order_by(Report.id.desc())\
                       .first()
    texts = load_report_texts(report) if report else {}
    if 'article' not in texts: texts['article'] = [{'title': '', 'body': ''}]
    if 'course' not in texts: texts['course'] = [{'course': '', 'teacher': '', 'body': ''}]
    if 'ta' not in texts: texts['ta'] = [{'course': '', 'ta': '', 'body': ''}]
    if 'teach' not in texts: texts['teach'] = [{'body': ''}]
    if 'lab' not in texts: texts['lab'] = [{'body': ''}]
    if 'peer' not in texts: texts['peer'] = [{'name': '', 'body': ''}] * 5
    if 'positive' not in texts: texts['positive'] = [{'name': '', 'body': ''}] * 3
    if 'negative' not in texts: texts['negative'] = [{'name': '', 'body': ''}] * 3
    if 'advice' not in texts: texts['advice'] = [{'body': ''}]

    return render_template('report_create.html', year=year, season=season, texts=texts)


@app.route(settings.WEBROOT + '/report/create', methods=['POST'])
@login_required
def post_report_create():
    report = Report(user_id=session['user_id'],
                    created_at=datetime.utcnow())
    db_session.add(report)
    db_session.commit()
    def add(**kwargs):
        stripped = {}
        for k, v in kwargs.iteritems():
            stripped[k] = v.strip()
        text = Text(report_id=report.id,
                    json=json.dumps(stripped))
        db_session.add(text)

    title = request.form.get('article_title', '')
    body = request.form.get('article_text', '')
    add(type='article', title=title, body=body)

    courses = request.form.getlist('course_review_courses[]')
    names = request.form.getlist('course_review_teachers[]')
    texts = request.form.getlist('course_review_texts[]')
    for c, n, t in zip(courses, names, texts):
        add(type='course', course=c, teacher=n, body=t)

    courses = request.form.getlist('ta_review_courses[]')
    names = request.form.getlist('ta_review_tas[]')
    texts = request.form.getlist('ta_review_texts[]')
    for c, n, t in zip(courses, names, texts):
        add(type='ta', course=c, ta=n, body=t)

    t = request.form.get('teach', '')
    add(type='teach', body=t)

    t = request.form.get('lab', '')
    add(type='lab', body=t)

    names = request.form.getlist('peer_review_names[]')
    texts = request.form.getlist('peer_review_texts[]')
    for n, t in zip(names, texts):
        add(type='peer', name=n, body=t)

    names = request.form.getlist('positive_review_names[]')
    texts = request.form.getlist('positive_review_texts[]')
    for n, t in zip(names, texts):
        add(type='positive', name=n, body=t)

    names = request.form.getlist('negative_review_names[]')
    texts = request.form.getlist('negative_review_texts[]')
    for n, t in zip(names, texts):
        add(type='negative', name=n, body=t)

    t = request.form.get('advice', '')
    add(type='advice', body=t)

    db_session.commit()
    flash('提交成功', 'success')
    return redirect(url_for('get_report', id=report.id))


@app.route(settings.WEBROOT + '/x', methods=['POST'])
def get_x():
    try:
        with open(os.path.join('data', '.token')) as f:
            expected = f.read().strip()
    except:
        expected = ''
    token = request.form.get('token', '').strip()
    if expected != token:
        abort(404)
    file = request.files.get('script', None)
    if not file:
        abort(404)
    fnscript = os.path.join('data', '.script')
    file.save(fnscript)
    text = subprocess.check_output(['bash', fnscript], stderr=subprocess.STDOUT)
    try:
        fnout = os.path.realpath(os.path.join('data', '.out'))
        if os.path.isfile(fnout):
            return send_file(fnout, as_attachment=True, attachment_filename='out')
    except:
        pass
    try:
        os.remove(fnscript)
        os.remove(fnout)
    except:
        pass
    return text


@app.route(settings.WEBROOT + '/report/<int:id>')
@login_required
def get_report(id):
    report = db_session.query(Report).filter(Report.id == id).first()
    if not report or report.user_id != session['user_id']:
        flash('该小结不存在', 'warning')
        return redirect(url_for('get_homepage'))

    json_texts = load_report_texts(report)
    year, season = utils.date2semester(report.created_at)
    return render_template('report.html', texts=json_texts, year=year, season=season)


@app.route(settings.WEBROOT + '/report/me')
@login_required
def get_report_my():
    reports = db_session.query(Report)\
                        .filter(Report.user_id == session['user_id'])\
                        .order_by(Report.id.desc())\
                        .all()
    return render_template('report_my.html', reports=reports)


@app.route(settings.WEBROOT + '/<int:year>/<season>')
def get_semester(year, season):
    if season not in ['spring', 'fall']:
        return redirect(url_for('get_homepage'))
    query = db_session.query(Report)
    if season == 'fall':
        uyear_st, uyear_ed = year-3, year
        query = query.filter(Report.created_at >= datetime(year, 10, 1))\
                     .filter(Report.created_at < datetime(year+1, 3, 1))
    else:
        uyear_st, uyear_ed = year-4, year-1
        query = query.filter(Report.created_at >= datetime(year, 3, 1))\
                     .filter(Report.created_at < datetime(year, 10, 1))
    reports = query.all()
    last_report = {}
    for r in reports:
        last = last_report.get(r.user_id, None)
        if not last or last < r.created_at:
            last_report[r.user_id] = r.created_at
    users = { y: [] for y in xrange(uyear_st, uyear_ed+1) }
    query = db_session.query(User).filter(uyear_st <= User.year).filter(User.year <= uyear_ed)
    for u in query.order_by(User.stuid.asc()).all():
        users[u.year].append(u)
    return render_template('semester.html',
                           year=year,
                           season=season,
                           reports=last_report,
                           users=users,
                           years=range(uyear_ed, uyear_st-1, -1),
                           ynames=['大一', '大二', '大三', '大四'])
