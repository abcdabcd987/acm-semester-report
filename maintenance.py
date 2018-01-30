# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
import os
import io
import re
import sys
import copy
import time
import yaml
import json
import codecs
import hashlib
import traceback
from pprint import pprint
from datetime import datetime
import acm_report.utils as utils
from acm_report.models import *
from acm_report.database import db_session, init_db


def read(prompt):
    return raw_input(prompt).strip().decode('utf-8')


def initdb():
    key = int(time.time()) // 60
    key = hashlib.md5(str(key)).hexdigest()[:6]
    if len(sys.argv) != 3 or sys.argv[2] != key:
        print('please run the following command within the current minute')
        print('    python maintenance.py initdb %s' % key)
        sys.exit(1)
    print('initializing the database')
    init_db()
    print('done!')


def change_email():
    if len(sys.argv) != 4:
        print('usage: python maintenance.py change_email <stuid> <email>')
        sys.exit(1)
    stuid = sys.argv[2]
    email = sys.argv[3]
    user = db_session.query(User).filter(User.stuid == stuid).one()
    user.email = email
    db_session.commit()
    print('done! %s %s %s %s' % (user.name, user.email, user.year, user.stuid))


def add_users():
    if len(sys.argv) != 3:
        print('usage: python maintenance.py add_users <path to new user list>')
        sys.exit(1)
    cnt = 0
    with open(sys.argv[2], 'rb') as f:
        for line in f:
            line = line.decode('utf-8').strip()
            if line.startswith('#') or not line:
                continue
            name, email, year, stuid = line.split()
            user = User(name=name, email=email, year=year, stuid=stuid)
            db_session.add(user)
            cnt += 1
    db_session.commit()
    print('done! %d new users added' % cnt)


def generate():
    try:
        year = int(sys.argv[2])
        season = sys.argv[3]
        if season not in ['spring', 'fall']:
            raise
    except:
        print('usage: python maintenance.py generate <year> <season>')
        print('e.g.   python maintenance.py generate %d %s' % utils.date2semester(datetime.utcnow()))
        sys.exit(1)

    basename = '%d%s' % (year, season)
    basedir = os.path.join('data', basename)
    os.mkdir(basedir)

    # fetch data
    print('fetching data...')
    query = db_session.query(Report)
    if season == 'fall':
        uyear_st, uyear_ed = year-3, year
        query = query.filter(Report.created_at >= datetime(year, 10, 1))\
                     .filter(Report.created_at < datetime(year+1, 3, 1))
    else:
        uyear_st, uyear_ed = year-4, year-1
        query = query.filter(Report.created_at >= datetime(year, 3, 1))\
                     .filter(Report.created_at < datetime(year, 10, 1))
    year2str = { y: ['大一', '大二', '大三', '大四'][i] for i, y in zip(xrange(0, 4), xrange(uyear_ed, uyear_st-1, -1)) }
    reports = query.all()
    last_report = {}
    for r in reports:
        last = last_report.get(r.user_id, None)
        if not last or last.created_at < r.created_at:
            last_report[r.user_id] = r
    users = { y: [] for y in xrange(uyear_st, uyear_ed+1) }
    query = db_session.query(User).filter(uyear_st <= User.year).filter(User.year <= uyear_ed)
    texts = {}
    for u in query.order_by(User.stuid.asc()).all():
        users[u.year].append(u)
        r = last_report.get(u.id, None)
        if r:
            texts[r.id] = load_report_texts(r)

    # 整份小结
    print('generating full text...')
    dirname = os.path.join(basedir, '0整份小结')
    os.mkdir(dirname)
    for y in xrange(uyear_st, uyear_ed+1):
        d = os.path.join(dirname, 'ACM%d%s' % (y, year2str[y]))
        os.mkdir(d)
        for u in users[y]:
            r = last_report.get(u.id, None)
            if not r:
                continue
            t = texts[r.id]
            with codecs.open(os.path.join(d, '%s.txt' % u.name), 'w', 'utf-8') as f:
                f.write('# ACM%d-%s %s\n\n' % (u.year, u.name, utils.semester_name(year, season)))

                f.write('## 1. 正文部分\n\n')
                try:
                    f.write(t['article'][0]['title'] + '\n\n')
                    f.write(utils.normalize_nl(t['article'][0]['body']) + '\n\n')
                except:
                    pass

                f.write('## 2. 课程评价\n\n')
                try:
                    for x in t['course']:
                        f.write('### %s - %s\n\n' % (x['course'], x['teacher']))
                        f.write(utils.normalize_nl(x['body']) + '\n\n')
                except:
                    pass

                f.write('## 3. 助教评价\n\n')
                try:
                    for x in t['ta']:
                        f.write('### %s - %s\n\n' % (x['course'], x['ta']))
                        f.write(utils.normalize_nl(x['body']) + '\n\n')
                except:
                    pass

                f.write('## 4. 助教工作小结\n\n')
                try:
                    f.write(utils.normalize_nl(t['teach'][0]['body']) + '\n\n')
                except:
                    pass

                # f.write('## 5. 实验室实习小结\n\n')
                # try:
                #     f.write(utils.normalize_nl(t['lab'][0]['body']) + '\n\n')
                # except:
                #     pass

                f.write('## 5. 同学评价\n\n')
                try:
                    for x in t['peer']:
                        f.write('### %s\n\n' % x['name'])
                        f.write(utils.normalize_nl(x['body']) + '\n\n')
                except:
                    pass

                f.write('## 6. 同学好评\n\n')
                try:
                    for x in t['positive']:
                        f.write('### %s\n\n' % x['name'])
                        f.write(utils.normalize_nl(x['body']) + '\n\n')
                except:
                    pass

                f.write('## 7. 同学差评\n\n')
                try:
                    for x in t['negative']:
                        f.write('### %s\n\n' % x['name'])
                        f.write(utils.normalize_nl(x['body']) + '\n\n')
                except:
                    pass

                f.write('## 8. 班级建议\n\n')
                try:
                    f.write(utils.normalize_nl(t['advice'][0]['body']) + '\n\n')
                except:
                    pass

    # 1. 正文部分
    print('generating articles...')
    dirname = os.path.join(basedir, '1正文部分')
    os.mkdir(dirname)
    for y in xrange(uyear_st, uyear_ed+1):
        d = os.path.join(dirname, 'ACM%d%s' % (y, year2str[y]))
        os.mkdir(d)
        for u in users[y]:
            r = last_report.get(u.id, None)
            if not r: continue
            t = texts[r.id]
            try:
                title = t['article'][0]['title']
                body = t['article'][0]['body']
                if title and body:
                    with codecs.open(os.path.join(d, '%s.txt' % u.name), 'w', 'utf-8') as f:
                        f.write('## %s\n\n' % title)
                        f.write(utils.normalize_nl(body))
            except:
                print('error when dealing with ACM%d-%s' % (u.year, u.name))
                traceback.print_exc()

    # 2. 课程评价
    print('generating courses...')
    dirname = os.path.join(basedir, '2课程评价')
    os.mkdir(dirname)
    for y in xrange(uyear_st, uyear_ed+1):
        with codecs.open(os.path.join(dirname, 'ACM%d%s.txt' % (y, year2str[y])), 'w', 'utf-8') as f:
            for u in users[y]:
                r = last_report.get(u.id, None)
                if not r: continue
                t = texts[r.id]
                try:
                    if t['course']:
                        f.write('## ACM%d-%s\n\n' % (u.year, u.name))
                        for x in t['course']:
                            f.write('### %s - %s\n\n' % (x['course'], x['teacher']))
                            f.write(utils.normalize_nl(x['body']) + '\n\n')
                        f.write('\n\n\n')
                except:
                    print('error when dealing with ACM%d-%s' % (u.year, u.name))
                    traceback.print_exc()

    # 3. 助教评价
    print('generating TAs...')
    dirname = os.path.join(basedir, '3助教评价')
    os.mkdir(dirname)
    for y in xrange(uyear_st, uyear_ed+1):
        with codecs.open(os.path.join(dirname, 'ACM%d%s.txt' % (y, year2str[y])), 'w', 'utf-8') as f:
            for u in users[y]:
                r = last_report.get(u.id, None)
                if not r: continue
                t = texts[r.id]
                try:
                    if t['ta']:
                        f.write('## ACM%d-%s\n\n' % (u.year, u.name))
                        for x in t['ta']:
                            f.write('### %s - %s\n\n' % (x['course'], x['ta']))
                            f.write(utils.normalize_nl(x['body']) + '\n\n')
                        f.write('\n\n\n')
                except:
                    print('error when dealing with ACM%d-%s' % (u.year, u.name))
                    traceback.print_exc()

    # 4. 助教工作小结
    print('generating teachings...')
    dirname = os.path.join(basedir, '4助教工作小结')
    os.mkdir(dirname)
    for y in xrange(uyear_st, uyear_ed+1):
        for u in users[y]:
            try:
                r = last_report.get(u.id, None)
                t = texts[r.id]
                body = t['teach'][0]['body']
                with codecs.open(os.path.join(dirname, 'ACM%d-%s.txt' % (u.year, u.name)), 'w', 'utf-8') as f:
                    f.write(utils.normalize_nl(body))
            except:
                pass

    # # 5. 实验室实习小结
    # print('generating labs...')
    # dirname = os.path.join(basedir, '5实验室实习小结')
    # os.mkdir(dirname)
    # for y in xrange(uyear_st, uyear_ed+1):
    #     filename = os.path.join(dirname, 'ACM%d%s.txt' % (y, year2str[y]))
    #     with codecs.open(filename, 'w', 'utf-8') as f:
    #         for u in users[y]:
    #             r = last_report.get(u.id, None)
    #             if not r: continue
    #             t = texts[r.id]
    #             try:
    #                 body = t['lab'][0]['body']
    #                 if body:
    #                     f.write('## ACM%d-%s\n\n' % (u.year, u.name))
    #                     f.write(utils.normalize_nl(body) + '\n\n\n\n')
    #             except:
    #                 print('error when dealing with ACM%d-%s' % (u.year, u.name))
    #                 traceback.print_exc()

    # peer/positive/negative review
    print('building peer/positive/negative review map...')
    review_types = ['peer', 'positive', 'negative']
    review_name = ['同学评价', '同学好评', '同学差评']
    review = { k: {} for k in review_types }
    for y in xrange(uyear_st, uyear_ed+1):
        for k in review_types:
            review[k][y] = {}
        for u in users[y]:
            r = last_report.get(u.id, None)
            if not r: continue
            t = texts[r.id]
            try:
                for k in review_types:
                    for x in t[k]:
                        key = x['name']
                        if key not in review[k][y]:
                            review[k][y][key] = []
                        review[k][y][key].append({ 'from': u.name, 'body': x['body'] })
            except:
                print('error when dealing with ACM%d-%s' % (u.year, u.name))
                traceback.print_exc()

    for i, (k, kname) in enumerate(zip(review_types, review_name)):
        print('generating %s reviews...' % k)
        dirname = os.path.join(basedir, '%d%s' % (i+5, kname))
        os.mkdir(dirname)
        for y in xrange(uyear_st, uyear_ed+1):
            filename = os.path.join(dirname, 'ACM%d%s.txt' % (y, year2str[y]))
            with codecs.open(filename, 'w', 'utf-8') as f:
                rs = review[k][y]
                for name, reviews in rs.iteritems():
                    if reviews:
                        f.write('## %s\n\n' % name)
                        for r in reviews:
                            f.write('### 来自%s的%s\n' % (r['from'], kname))
                            f.write(utils.normalize_nl(r['body']) + '\n\n')
                        f.write('\n\n\n')

    # 9. 班级建议
    print('generating labs...')
    dirname = os.path.join(basedir, '8班级建议')
    os.mkdir(dirname)
    for y in xrange(uyear_st, uyear_ed+1):
        filename = os.path.join(dirname, 'ACM%d%s.txt' % (y, year2str[y]))
        with codecs.open(filename, 'w', 'utf-8') as f:
            for u in users[y]:
                r = last_report.get(u.id, None)
                if not r: continue
                t = texts[r.id]
                try:
                    body = t['advice'][0]['body']
                    if body:
                        f.write('## ACM%d-%s\n\n' % (u.year, u.name))
                        f.write(utils.normalize_nl(body) + '\n\n\n\n')
                except:
                    print('error when dealing with ACM%d-%s' % (u.year, u.name))
                    traceback.print_exc()


    # finalize
    print('cleaning zero byte files...')
    os.system('find %s -type f -size 0 -exec rm {} \;' % basedir)
    print('converting to CRLF...')
    os.system('find %s -type f -exec unix2dos {} \;' % basedir)
    print('archiving...')
    os.system('7z a data/%s.7z %s' % (basename, basedir))
    filename = os.path.join(basedir, 'packed_' + basename + '.7z')
    os.system('mv data/%s.7z %s' % (basename, filename))
    print('done!')
    print('saved  at', basedir)
    print('packed at', filename)


def validate_form(config):
    is_jinja = re.compile(r'({{.*?}})|({%.*?%})')
    config = copy.deepcopy(config)

    title = config.pop('title')
    assert type(title) in [str, unicode]
    start_time = config.pop('start_time')
    assert type(start_time) is datetime
    end_time = config.pop('end_time')
    assert type(end_time) is datetime
    assert start_time < end_time
    students = config.pop('students')
    assert type(students) is list
    for student in students:
        assert type(student) is int
    sections = config.pop('sections')
    assert type(sections) is list
    assert not config

    section_ids = []
    for section in sections:
        title = section.pop('title')
        assert type(title) in [str, unicode]
        id = section.pop('id')
        assert type(id) in [str, unicode]
        assert id not in section_ids
        section_ids.append(id)
        description = section.pop('description', '')
        assert type(description) in [str, unicode]
        fields = section.pop('fields')
        assert type(fields) is list
        reports = section.pop('reports')
        assert type(reports) is list
        if 'repeat' in section:
            repeat = section.pop('repeat')
            assert type(repeat) is dict
        else:
            repeat = None
        assert not section

        field_ids = []
        for field in fields:
            assert type(field) is dict
            id = field.pop('id')
            assert type(id) in [str, unicode]
            assert id not in field_ids
            field_ids.append(id)
            type_ = field.pop('type')
            assert type_ in ['string', 'text']
            if type_ == 'text':
                rows = field.pop('rows')
                assert type(rows) is int
            label = field.pop('label')
            assert type(label) in [str, unicode]
            assert not field
        assert len(field_ids) == len(fields)

        if repeat:
            min = repeat.pop('min')
            assert type(min) is int
            assert not repeat

        for report in reports:
            assert type(report) is dict
            file_by = report.pop('file_by')
            assert file_by in ['per_student', 'per_class']
            directory = report.pop('directory')
            assert type(directory) in [str, unicode]
            assert not is_jinja.match(directory)
            tostring = report.pop('tostring')
            assert type(tostring) in [str, unicode]
            if 'reductions' in report:
                reductions = report.pop('reductions')
                assert type(reductions) is dict
                for reduction in reductions.values():
                    assert type(reduction) is dict
                    key = reduction.pop('key')
                    assert not is_jinja.match(key)
                    assert type(key) in [str, unicode]
                    value = reduction.pop('value')
                    assert type(value) in [str, unicode]
                    assert not is_jinja.match(value)
                    assert not reduction
            assert not report


def set_form(filename, form):
    with io.open(filename, 'r', encoding='utf-8') as f:
        config_str = f.read()
    config = yaml.load(config_str)
    validate_form(config)

    form.title = config['title']
    form.start_time = config['start_time']
    form.end_time = config['end_time']
    form.config_yaml = config_str
    db_session.add(form)
    db_session.commit()
    print('success! the form id is:', form.id)


def add_form():
    if len(sys.argv) != 3:
        print('usage: python maintenance.py add_form <path to yaml>')
        sys.exit(1)
    form = Form()
    set_form(sys.argv[2], form)


def update_form():
    if len(sys.argv) != 4:
        print('usage: python maintenance.py update_form <form_id> <path to yaml>')
        sys.exit(1)
    form_id = int(sys.argv[2])
    form = db_session.query(Form).filter(Form.id == form_id).one()
    set_form(sys.argv[3], form)


if __name__ == '__main__':
    actions = {
        'initdb': initdb,
        'add_users': add_users,
        'change_email': change_email,
        'generate': generate,
        'add_form': add_form,
        'update_form': update_form,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in actions:
        print('usage: python maintenance.py ACTION')
        print('ACTION can be:')
        for k in actions:
            print('    %s' % k)
        sys.exit(1)
    actions[sys.argv[1]]()
