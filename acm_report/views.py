# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid
import functools
import pypinyin
from datetime import datetime
from flask import request, redirect, session, url_for, flash, render_template
from acm_report import app
from acm_report.models import *
from acm_report.database import db_session
import acm_report.email_queue as email_queue
import acm_report.settings as settings


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登入', 'warning')
            return redirect(url_for('get_login'))
        return f(*args, **kwargs)
    return decorated_function


def guest_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            flash('您已登入', 'warning')
            return redirect(url_for('get_homepage'))
        return f(*args, **kwargs)
    return decorated_function


def set_session_user(user):
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_category'] = user.category


def unset_session_user():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_category', None)


@app.route('/')
def get_homepage():
    return render_template('homepage.html')


@app.route('/login')
@guest_required
def get_login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
@guest_required
def post_login():
    email = request.form['email']
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        flash('没有找到 %s 对应的用户' % email, 'warning')
        return redirect(url_for('get_login'))

    # TODO: frequency limitation

    vericode = uuid.uuid4().hex
    lv = LoginVerification(
        user_id=user.id,
        code=vericode,
        valid=True,
        created_at=datetime.utcnow())
    db_session.add(lv)
    db_session.commit()

    date = settings.TIMEZONE.fromutc(lv.created_at.replace(tzinfo=settings.TIMEZONE))
    date = date.strftime('%Y-%m-%d %H:%M:%S')
    url = url_for('get_login_vericode', vericode=vericode)
    content = settings.EMAIL_TMPL_LOGIN_CONTENT.format(
        name=user.name,
        date=date,
        url=url)
    email_queue.send(email, settings.EMAIL_TMPL_LOGIN_SUBJECT, content)

    return render_template('login_verify.html', user=user)


@app.route('/login/vericode/<vericode>')
@guest_required
def get_login_vericode(vericode):
    query = db_session.query(LoginVerification).filter(LoginVerification.code == vericode)
    lv = query.first()
    err = ''
    if not err and not lv:
        err = '找不到该验证码'
    if not err and not lv.valid:
        err = '该验证码已经被使用'
    if not err:
        expire = lv.created_at + settings.LOGIN_VERICODE_EXPIRE
        if expire < datetime.utcnow():
            err = '该验证码已过期'
    if err:
        flash(err, 'warning')
        return redirect(url_for('get_login'))

    lv.valid = False
    db_session.commit()

    set_session_user(lv.user)
    return redirect(url_for('get_homepage'))


@app.route('/logout')
@login_required
def get_logout():
    unset_session_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('get_homepage'))


@app.route('/user/modify')
@login_required
def get_user_modify():
    user = db_session.query(User).filter(User.id == session['user_id']).first()
    if not user:
        flash('找不到该用户，请重新登入', 'warning')
        unset_session_user()
        return redirect(url_for('get_login'))
    return render_template('user_modify.html', user=user)


@app.route('/user/modify', methods=['POST'])
@login_required
def post_user_modify():
    id = request.form.get('id', None)
    if not id:
        flash('找不到该用户ID', 'warning')
        return redirect(url_for('get_user_modify'))
    user = db_session.query(User).filter(User.id == session['user_id']).first()
    if not user:
        flash('找不到该用户', 'warning')
        return redirect(url_for('get_user_modify'))

    stuid = request.form.get('stuid', user.stuid)
    name = request.form.get('name', user.name)
    pinyin = request.form.get('pinyin', user.pinyin)
    email = request.form.get('email', user.email)
    category = request.form.get('category', user.category)
    dropped = 'dropped' in request.form
    allow_login = 'allow_login' in request.form

    # TODO: allow priviledged user to modify more info
    user.pinyin = pinyin
    user.email = email
    db_session.commit()
    set_session_user(user)
    flash('修改成功', 'success')

    print(id, stuid, name, pinyin, email, category, dropped, allow_login)  # to please flake8
    return render_template('user_modify.html', user=user)


@app.route('/manage/batch-add-users')
@login_required
def get_manage_batch_add_users():
    status = session.pop('manage_batch_add_users_status', 0)
    users = session.pop('manage_batch_add_users_users', [])
    return render_template('manage_batch_add_users.html', status=status, users=users)


@app.route('/manage/batch-add-users', methods=['POST'])
@login_required
def post_manage_batch_add_users():
    category = request.form.get('category', '').strip()
    if not category:
        flash('入学年份不能为空', 'warning')
        return redirect(url_for('get_manage_batch_add_users'))
    text = request.form.get('text', '').strip()
    users = []
    for line in text.split('\n'):
        splited = line.split()
        if not splited:
            continue
        if len(splited) != 3:
            flash('格式错误：<code>%s</code>' % line, 'warning')
            return redirect(url_for('get_manage_batch_add_users'))
        pinyin = pypinyin.pinyin(splited[1], heteronym=False, style=pypinyin.NORMAL, errors='ignore')
        pinyin = ' '.join(x[0] for x in pinyin)
        users.append(User(name=splited[1],
                          pinyin=pinyin,
                          stuid=splited[0],
                          email=splited[2],
                          category=category,
                          dropped=False,
                          allow_login=True))
    status = request.form.get('status', '0')
    if status != '1':
        flash('请确认以下信息是否正确，然后点击注册', 'warning')
        return render_template('manage_batch_add_users.html', status=1, users=users, category=category, text=text)
    user_dicts = []
    for u in users:
        db_session.add(u)
        user_dicts.append({'name': u.name, 'pinyin': u.pinyin, 'stuid': u.stuid, 'email': u.email})
    db_session.commit()
    # TODO: commit failure
    flash('批量添加用户成功', 'success')
    session['manage_batch_add_users_status'] = 2
    session['manage_batch_add_users_users'] = user_dicts
    return redirect(url_for('get_manage_batch_add_users'))
