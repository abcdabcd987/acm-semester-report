import pytz
import datetime

class Settings:
    SECRET_KEY = 'you can copy from: python -c "print(repr(__import__(\"os\").urandom(30)))"'
    TIMEZONE = pytz.timezone('Asia/Shanghai')
    WEBROOT = '/report'
    SQLALCHEMY_DATABASE_URI = 'sqlite:////Users/abcdabcd987/Developer/acm-semester-report/data/report.db'
