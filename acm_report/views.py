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
import acm_report.utils as utils


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

    date = utils.format_from_utc(lv.created_at)
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


@app.route('/user/list')
@login_required
def get_user_list():
    id = request.args.get('id', '')
    stuid = request.args.get('stuid', '')
    name = request.args.get('name', '')
    category = request.args.get('category', 'None')
    dropped = request.args.get('dropped', '')
    allow_login = request.args.get('allow_login', '')
    dropped = dropped == 'True' if dropped in ['True', 'False'] else None
    allow_login = allow_login == 'True' if allow_login in ['True', 'False'] else None

    query = db_session.query(User)
    try:
        id = int(id)
        query = query.filter(User.id == id)
    except:
        pass
    if stuid:
        query = query.filter(User.stuid == stuid)
    if name:
        query = query.filter(User.name == name)
    if category != 'None':
        query = query.filter(User.category == category)
    if dropped is not None:
        query = query.filter(User.dropped.is_(dropped))
    if allow_login is not None:
        query = query.filter(User.allow_login.is_(dropped))

    users = query.order_by(User.id.desc()).all()
    categories = db_session.query(User.category).distinct().all()
    tasks = db_session.query(Task).filter(Task.deadline > datetime.utcnow()).all()
    return render_template('user_list.html', users=users, categories=categories, tasks=tasks)


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


@app.route('/task/new')
@login_required
def get_task_new():
    title = session.pop('get_task_new_title', '')
    deadline = session.pop('get_task_new_title', '')
    return render_template('task_edit_basic_info.html', title=title, deadline=deadline)


@app.route('/task/new', methods=["POST"])
@login_required
def post_task_new():
    title = request.form.get('title', '').strip()
    deadline = request.form.get('deadline', '').strip()
    err = None
    try:
        deadline = utils.parse_datetime(deadline)
        deadline = utils.local_to_utc(deadline)
    except:
        err = '截止日期格式不正确'
    if not title:
        err = '标题不能为空'
    if err:
        flash(err, 'warning')
        session['get_task_new_title'] = title
        session['get_task_new_deadline'] = request.form.get('deadline', '').strip()
        return redirect(url_for('get_task_new'))
    task = Task(title=title, deadline=deadline, published=False)
    db_session.add(task)
    db_session.commit()
    return redirect(url_for('get_task_info', id=task.id))


@app.route('/task/list')
@login_required
def get_task_list():
    tasks = db_session.query(Task).order_by(Task.id.desc()).all()
    return render_template('task_list.html', tasks=tasks)


@app.route('/task/<int:id>/info')
@login_required
def get_task_info(id):
    task = db_session.query(Task).filter(Task.id == id).first()
    if not task:
        flash('找不到该任务', 'warning')
        return redirect(url_for('get_task_list'))
    return render_template('task_info.html',
                           task=task,
                           users=task.users,
                           requirements=task.requirements)


@app.route('/task/add_users', methods=['POST'])
@login_required
def post_task_add_users():
    selected = request.form.get('selected', '').split('|')
    id = request.form.get('taskid', None)
    try:
        id = int(id)
    except:
        pass
    task = db_session.query(Task).filter(Task.id == id).first()
    err = None
    if not selected:
        err = '没有选中的用户'
    if not task:
        err = '找不到该任务'
    if not err and task.deadline < datetime.utcnow():
        err = '该任务已过截止日期'
    if err:
        flash(err, 'warning')
        return redirect(url_for('get_user_list'))

    for u in task.users:
        uid = str(u.id)
        if uid in selected:
            selected.remove(uid)

    users = db_session.query(User).filter(User.id.in_(selected)).all()
    if len(users) != len(selected):
        flash('某个用户不存在于数据库中', 'warning')
        return redirect(url_for('get_user_list'))
    task.users.extend(users)
    db_session.commit()

    flash('添加用户成功', 'success')
    return redirect(url_for('get_task_info', id=task.id))


def check_task_requirement_config(config, type):
    allowed_keys = {
        TaskRequirementType.freetext: {'title'},
        TaskRequirementType.ta_review: {'title', 'num'},
        TaskRequirementType.course_review: {'title', 'num'},
        TaskRequirementType.peer_review: {'title', 'num', 'type'},
    }
    for c in config.split('|'):
        splited = c.split(':')
        if len(splited) != 2:
            return False
        k, v = splited[0].strip(), splited[1].strip()
        if k not in allowed_keys[type]:
            return False
        if k == 'num':
            try:
                v = int(v)
            except:
                return False
        elif k == 'type':
            if v not in PeerReviewType.__members__:
                return False
    return True


@app.route('/task/task_add_requirement', methods=['POST'])
@login_required
def post_task_add_requirement():
    id = request.form.get('id', None)
    type = request.form.get('type', '')
    config = request.form.get('config', '')
    try:
        id = int(id)
    except:
        pass
    task = db_session.query(Task).filter(Task.id == id).first()
    err = None
    if not task:
        err = '找不到该任务'
    if not err and task.deadline < datetime.utcnow():
        err = '该任务已过截止日期'
    if type not in TaskRequirementType.__members__:
        err = '没有类型为 %s 的任务' % type
    else:
        type = TaskRequirementType[type]
    if not err and not check_task_requirement_config(config, type):
        err = 'config 格式不正确'
    if err:
        flash(err, 'warning')
        return redirect(url_for('get_task_info', id=id))

    r = TaskRequirement(type=type,
                        task_id=task.id,
                        order=len(task.requirements) + 1,
                        config=config)
    task.requirements.append(r)
    db_session.commit()
    flash('成功添加任务', 'success')
    return redirect(url_for('get_task_info', id=id))
