import pytz
import datetime

class Settings:
    SECRET_KEY = 'you can copy from: python -c "print(repr(__import__(\"os\").urandom(30)))"'
    TIMEZONE = pytz.timezone('Asia/Shanghai')
    WEBROOT = '/report'
    SQLALCHEMY_DATABASE_URI = 'sqlite:////Users/abcdabcd987/Developer/acm-semester-report/data/report.db'
    MAIL_FROM = 'noreply@acm.ac.cn'
    MAIL_FROM_NAME = 'ACM班学期小结'
    MAIL_BODY = '你好，{name}！\n你正在登入ACM班学期小结，你的验证码是：\n{vericode}\n'
    MAIL_SUBJECT = 'ACM班学期小结验证邮件'
    SUPER_USERS = ["5140309565"]
