from __future__ import print_function, division
import sys
import time
import hashlib
import pypinyin
import acm_report.database as db
import acm_report.models as models


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


def read(prompt):
    return raw_input(prompt).strip().decode('utf-8')


def create_admin():
    print('creating admin account. please provide the following informations.')
    name = read('Name: ')
    stuid = read('StudentID: ')
    email = read('Email: ')
    category = read('Category (e.g. 2014): ')
    print('got it:', name, stuid, email, category)
    confirm = read('is the above info correct? [y/n] ')
    if confirm != 'y':
        print('given up')
        sys.exit(1)

    pinyin = pypinyin.pinyin(name, heteronym=False, style=pypinyin.NORMAL, errors='ignore')
    pinyin = ' '.join(x[0] for x in pinyin)
    user = models.User(name=name,
                       pinyin=pinyin,
                       stuid=stuid,
                       email=email,
                       category=category,
                       dropped=False,
                       allow_login=True)
    db.db_session.add(user)
    db.db_session.commit()
    print('done!')


if __name__ == '__main__':
    actions = {
        'initdb': initdb,
        'create_admin': create_admin
    }
    if len(sys.argv) < 2 or sys.argv[1] not in actions:
        print('usage: python maintenance.py ACTION')
        print('ACTION can be:')
        for k in actions:
            print('    %s' % k)
        sys.exit(1)
    actions[sys.argv[1]]()
