# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytz
import datetime

LOGIN_VERICODE_EXPIRE = datetime.timedelta(minutes=10)
WEBSITE_URL = 'https://acm.sjtu.edu.cn/report'
EMAIL_ADMIN = 'i@abcdabcd987.com'
FLASK_SECRET_KEY = 'you can copy from: python -c "print(repr(__import__(\"os\").urandom(30)))"'
TIMEZONE = pytz.timezone('Asia/Shanghai')

EMAIL_TMPL_LOGIN_SUBJECT = '您正在登入ACM班期末小结网站'
EMAIL_TMPL_LOGIN_CONTENT = '''{{name}}您好：

您的帐户在 {{date}} 请求登入ACM班期末小结网站。如果这是您本人的操作，请访问下面这个网址，之后您可以在当前浏览器登入网站： {webroot}{{url}}

如果这不是您本人的操作，请忽略此邮件。如果您持续收到这样的邮件，请报告管理员：{admin}
'''.format(webroot=WEBSITE_URL, admin=EMAIL_ADMIN)
