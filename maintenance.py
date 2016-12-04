# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
import os
import sys
import time
import json
import codecs
import hashlib
import traceback
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

                f.write('## 5. 实验室实习小结\n\n')
                try:
                    f.write(utils.normalize_nl(t['lab'][0]['body']) + '\n\n')
                except:
                    pass

                f.write('## 6. 同学评价\n\n')
                try:
                    for x in t['peer']:
                        f.write('### %s\n\n' % x['name'])
                        f.write(utils.normalize_nl(x['body']) + '\n\n')
                except:
                    pass

                f.write('## 7. 同学好评\n\n')
                try:
                    for x in t['positive']:
                        f.write('### %s\n\n' % x['name'])
                        f.write(utils.normalize_nl(x['body']) + '\n\n')
                except:
                    pass

                f.write('## 8. 同学差评\n\n')
                try:
                    for x in t['negative']:
                        f.write('### %s\n\n' % x['name'])
                        f.write(utils.normalize_nl(x['body']) + '\n\n')
                except:
                    pass

                f.write('## 9. 班级建议\n\n')
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

    # 5. 实验室实习小结
    print('generating labs...')
    dirname = os.path.join(basedir, '5实验室实习小结')
    os.mkdir(dirname)
    for y in xrange(uyear_st, uyear_ed+1):
        filename = os.path.join(dirname, 'ACM%d%s.txt' % (y, year2str[y]))
        with codecs.open(filename, 'w', 'utf-8') as f:
            for u in users[y]:
                r = last_report.get(u.id, None)
                if not r: continue
                t = texts[r.id]
                try:
                    body = t['lab'][0]['body']
                    if body:
                        f.write('## ACM%d-%s\n\n' % (u.year, u.name))
                        f.write(utils.normalize_nl(body) + '\n\n\n\n')
                except:
                    print('error when dealing with ACM%d-%s' % (u.year, u.name))
                    traceback.print_exc()

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
        dirname = os.path.join(basedir, '%d%s' % (i+6, kname))
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
    dirname = os.path.join(basedir, '9班级建议')
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
    print('archiving...')
    os.system('7z a data/%s.7z %s' % (basename, basedir))
    filename = os.path.join(basedir, 'packed_' + basename + '.7z')
    os.system('mv data/%s.7z %s' % (basename, filename))
    print('done!')
    print('saved  at', basedir)
    print('packed at', filename)



if __name__ == '__main__':
    actions = {
        'initdb': initdb,
        'add_users': add_users,
        'generate': generate,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in actions:
        print('usage: python maintenance.py ACTION')
        print('ACTION can be:')
        for k in actions:
            print('    %s' % k)
        sys.exit(1)
    actions[sys.argv[1]]()
