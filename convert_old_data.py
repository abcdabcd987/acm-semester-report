import json
import sqlite3
from tqdm import tqdm
from datetime import datetime, timedelta


def connect(filename):
    conn = sqlite3.connect(filename, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def load_report_texts(conn_old, report_id):
    cur = conn_old.cursor()
    cur.execute('SELECT * FROM text WHERE report_id == ? ORDER BY id ASC', (report_id, ))
    json_texts = {}
    for text in cur.fetchall():
        t = json.loads(text['json'])
        for k, v in t.items():
            if v.strip() in ['N/A', 'NA', '无', '没有']:
                t[k] = ''
        key = t['type']
        if key not in json_texts:
            json_texts[key] = []
        json_texts[key].append(t)
    return json_texts


def convert(old_filename, new_filename, form_id, start_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = start_date + timedelta(days=120)
    conn_old = connect(old_filename)
    conn_new = connect(new_filename)

    cur_reports = conn_old.execute('SELECT * FROM reports WHERE created_at BETWEEN ? AND ? ORDER BY id ASC', (start_date, end_date))
    for old_report in tqdm(cur_reports.fetchall()):
        texts = load_report_texts(conn_old, old_report['id'])
        content = {
            'article': [{
                'title': texts['article'][0]['title'],
                'content': texts['article'][0]['body'],
            }],
            'course': [
                dict(course=x['course'], name=x['teacher'], content=x['body'])
                for x in texts['course']
            ],
            'ta': [
                dict(course=x['course'], name=x['ta'], content=x['body'])
                for x in texts['ta']
            ],
            'teach': [{
                'content': texts['teach'][0]['body']
            }],
            'peer_review': [
                dict(name=x['name'], content=x['body'])
                for x in texts['peer']
            ],
            'positive_review': [
                dict(name=x['name'], content=x['body'])
                for x in texts['positive']
            ],
            'negative_review': [
                dict(name=x['name'], content=x['body'])
                for x in texts['negative']
            ],
            'suggestion': [{
                'content': texts['advice'][0]['body']
            }],
        }
        conn_new.execute('INSERT INTO reports (id, user_id, form_id, json, created_at) VALUES (?, ?, ?, ?, ?)',
            (old_report['id'], old_report['user_id'], form_id, json.dumps(content), old_report['created_at']))


if __name__ == '__main__':
    convert('data/old.db', 'data/report.db', 1, '2017-01-01')
