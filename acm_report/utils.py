import pytz
import markdown
from datetime import datetime
from .settings import Settings


def format_from_utc(dt):
    dt = Settings.TIMEZONE.fromutc(dt.replace(tzinfo=Settings.TIMEZONE))
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def parse_datetime(value):
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')


def local_to_utc(local):
    return Settings.TIMEZONE.localize(local, is_dst=False).astimezone(pytz.utc)


def nl2p(text):
    return ''.join("<p>%s</p>" % line for line in text.splitlines() if line)


def normalize_nl(text):
    return '\n\n'.join(line for line in text.splitlines() if line)


def markdown_to_html5(text):
    return markdown.markdown(text, output_format='html5')

def is_super_user(stuid):
    return stuid and stuid in Settings.SUPER_USERS
