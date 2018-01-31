# -*- coding: utf-8 -*-

import pytz
import markdown
from datetime import datetime
import acm_report.settings as settings


def format_from_utc(dt):
    dt = settings.TIMEZONE.fromutc(dt.replace(tzinfo=settings.TIMEZONE))
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def parse_datetime(value):
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')


def local_to_utc(local):
    return settings.TIMEZONE.localize(local, is_dst=False).astimezone(pytz.utc)


def nl2p(text):
    return ''.join("<p>%s</p>" % line for line in text.splitlines() if line)


def normalize_nl(text):
    return '\n\n'.join(line for line in text.splitlines() if line)


def semester_name(year, season):
    if season == 'fall':
        return '%d-%d学年秋季学期' % (year, year+1)
    else:
        return '%d-%d学年春夏学期' % (year-1, year)


def date2semester(date):
    if 3 <= date.month < 10:
        return date.year, 'spring'
    if date.month < 3:
        return date.year-1, 'fall'
    else:
        return date.year, 'fall'


def markdown_to_html5(text):
    return markdown.markdown(text, output_format='html5')
