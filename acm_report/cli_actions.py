import os
import re
import sys
import copy
import time
import yaml
import json
import jinja2
import hashlib
import traceback
from pprint import pprint
from datetime import datetime
from . import utils
from .models import *


def change_email(stuid, email):
    user = db.session.query(User).filter(User.stuid == stuid).one()
    user.email = email
    db.session.commit()
    print('done! %s %s %s %s' % (user.name, user.email, user.year, user.stuid))


def add_users(filename):
    cnt = 0
    with open(filename, 'rb') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            name, email, year, stuid = line.split()
            user = User(name=name, email=email, year=year, stuid=stuid)
            db.session.add(user)
            cnt += 1
    db.session.commit()
    print('done! %d new users added' % cnt)


def generate(form_id):
    def is_empty_fields(fields):
        if type(fields) is list:
            return all(is_empty_fields(f) for f in fields)
        for k, v in fields.items():
            if v.strip():
                return False
        return True

    def load_section_json(latest_reports, user, section):
        section_json = json.loads(latest_reports[user.id].json)[section['id']]
        for field in section['fields']:
            if field['type'] == 'text':
                for f in section_json:
                    f[field['id']] = utils.normalize_nl(f[field['id']])
        return section_json

    form = db.session.query(Form).filter(Form.id == form_id).one()
    config = yaml.load(form.config_yaml)

    basename = '[{}]{}'.format(form.id, form.title)
    basedir = os.path.join('data', basename)
    os.mkdir(basedir)

    latest_reports = {}
    for r in db.session.query(Report).filter(Report.form_id == form_id):
        if r.user_id not in latest_reports or latest_reports[r.user_id].created_at < r.created_at:
            latest_reports[r.user_id] = r
    users = {r.id: r for r in db.session.query(User).filter(User.id.in_(latest_reports.keys()))}

    for section_index, section in enumerate(config['sections'], start=1):
        print(section['title'])
        ctx_section = {'index': section_index, 'title': section['title']}
        for report_config in section['reports']:
            dirname = report_config['directory'].format(section=ctx_section)
            dirname = os.path.join(basedir, dirname)
            os.mkdir(dirname)
            template = jinja2.Template(report_config['tostring'])

            if report_config['file_by'] == 'per_student':
                for u in users.values():
                    section_json = load_section_json(latest_reports, u, section)
                    if is_empty_fields(section_json):
                        continue
                    filename = 'ACM{}-{}.txt'.format(u.year, u.name)
                    with open(os.path.join(dirname, filename), 'w', encoding='utf-8') as f:
                        f.write(template.render(student=u.__dict__,
                                                section=ctx_section,
                                                fields=section_json))


            elif report_config['file_by'] == 'per_class':
                for year in config['students']:
                    students = []
                    for u in users.values():
                        if u.year != year:
                            continue
                        d = copy.deepcopy(u.__dict__)
                        section_json = load_section_json(latest_reports, u, section)
                        if is_empty_fields(section_json):
                            continue
                        d['fields'] = section_json
                        students.append(d)

                    reductions = {}
                    for var_name, kv in report_config.get('reductions', {}).items():
                        key_template = kv['key']
                        value_template = kv['value']
                        d = {}
                        for u in users.values():
                            if u.year != year:
                                continue
                            section_json = load_section_json(latest_reports, u, section)
                            for fields in section_json:
                                if is_empty_fields(fields):
                                    continue
                                key = key_template.format(fields=fields, section=ctx_section, student=u.__dict__)
                                value = value_template.format(fields=fields, section=ctx_section, student=u.__dict__)
                                if key not in d:
                                    d[key] = []
                                d[key].append(value)
                        reductions[var_name] = d

                    filename = 'ACM{}.txt'.format(year)
                    with open(os.path.join(dirname, filename), 'w', encoding='utf-8') as f:
                        f.write(template.render(students=students,
                                                section=ctx_section,
                                                reductions=reductions))
            else:
                assert False, 'unknown file_by field: ' + report_config['file_by']

    print('converting to CRLF...')
    os.system('find %s -type f -exec unix2dos {} \;' % basedir)
    print('archiving...')
    os.system('7z a data/%s.7z %s' % (basename, basedir))
    filename = os.path.join(basedir, 'packed_' + basename + '.7z')
    os.system('mv data/%s.7z %s' % (basename, filename))
    print('done!')
    print('saved  at', basedir)
    print('packed at', filename)


def flatten_deepcopy(config):
    if type(config) is dict:
        return {k: flatten_deepcopy(v) for k, v in config.items()}
    elif type(config) is list:
        return [flatten_deepcopy(v) for v in config]
    elif type(config) is set:
        return set(flatten_deepcopy(v) for v in config)
    else:
        return copy.copy(config)


def validate_form(config, debug_print):
    is_jinja = re.compile(r'({{.*?}})|({%.*?%})')
    config = flatten_deepcopy(config)

    title = config.pop('title')
    assert type(title) is str
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
        assert type(title) is str
        id = section.pop('id')
        debug_print(0, 'enter section', id)
        assert type(id) is str
        assert id not in section_ids
        section_ids.append(id)
        description = section.pop('description', '')
        assert type(description) is str
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
            debug_print(4, 'enter field', id)
            assert type(id) is str
            assert id not in field_ids
            field_ids.append(id)
            type_ = field.pop('type')
            assert type_ in ['string', 'text']
            if type_ == 'text':
                rows = field.pop('rows')
                assert type(rows) is int
            label = field.pop('label')
            assert type(label) is str
            assert not field
            debug_print(4, 'exit field')
        assert len(field_ids) == len(fields)

        if repeat:
            min = repeat.pop('min')
            assert type(min) is int
            assert not repeat

        for report in reports:
            debug_print(4, 'enter report')
            assert type(report) is dict
            file_by = report.pop('file_by')
            assert file_by in ['per_student', 'per_class']
            directory = report.pop('directory')
            assert type(directory) is str
            assert not is_jinja.match(directory)
            tostring = report.pop('tostring')
            assert type(tostring) is str
            if 'reductions' in report:
                reductions = report.pop('reductions')
                assert type(reductions) is dict
                for name, reduction in reductions.items():
                    debug_print(8, 'enter reduction', name)
                    assert type(name) is str
                    assert type(reduction) is dict
                    key = reduction.pop('key')
                    assert not is_jinja.match(key)
                    assert type(key) is str
                    value = reduction.pop('value')
                    assert type(value) is str
                    assert not is_jinja.match(value)
                    assert not reduction
                    debug_print(8, 'exit reduction')
            assert not report
            debug_print(4, 'exit report')
        debug_print(0, 'exit section')


def set_form(filename, form, debug):
    def debug_print(indent, *args, **kwargs):
        if debug:
            print(' '*indent, *args, **kwargs)

    with open(filename, 'r', encoding='utf-8') as f:
        config_str = f.read()
    config = yaml.load(config_str)
    validate_form(config, debug_print)

    form.title = config['title']
    form.start_time = config['start_time']
    form.end_time = config['end_time']
    form.config_yaml = config_str
    db.session.add(form)
    db.session.commit()
    print('success! the form id is:', form.id)


def add_form(filename, debug):
    form = Form()
    set_form(filename, form, debug)


def update_form(form_id, filename, debug):
    form_id = int(form_id)
    form = db.session.query(Form).filter(Form.id == form_id).one()
    set_form(filename, form, debug)
