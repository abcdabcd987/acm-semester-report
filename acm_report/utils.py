import pytz
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
