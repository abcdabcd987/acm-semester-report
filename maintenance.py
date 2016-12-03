from __future__ import print_function, division
import sys
import time
import hashlib
import pypinyin
import acm_report.database as db
import acm_report.models as models


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
    db.init_db()
    print('done!')


def add_users():
    if len(sys.argv) != 3:
        print('usage: python maintenance.py add_users new_user_list.txt')
        sys.exit(1)
    cnt = 0
    with open(sys.argv[2], 'rb') as f:
        for line in f:
            line = line.decode('utf-8').strip()
            if line.startswith('#') or not line:
                continue
            name, email, year, stuid = line.split()
            user = models.User(name=name, email=email, year=year, stuid=stuid)
            db.db_session.add(user)
            cnt += 1
    db.db_session.commit()
    print('done! %d new users added' % cnt)


if __name__ == '__main__':
    actions = {
        'initdb': initdb,
        'add_users': add_users
    }
    if len(sys.argv) < 2 or sys.argv[1] not in actions:
        print('usage: python maintenance.py ACTION')
        print('ACTION can be:')
        for k in actions:
            print('    %s' % k)
        sys.exit(1)
    actions[sys.argv[1]]()
