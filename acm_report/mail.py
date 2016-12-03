# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import smtplib
from email.mime.text import MIMEText
from email.header import Header


def send_vericode(to_addr, to_name, vericode):
    sender = 'noreply@acm.sjtu.edu.cn'
    text = '你好，%s！\n你正在登入ACM班学期小结，你的验证码是：\n%s\n' % (to_name, vericode)
    msg = MIMEText(text, 'plain', 'utf-8')
    msg['Subject'] = Header('ACM班学期小结验证邮件', 'utf-8')
    msg['From'] = Header('ACM班学期小结', 'utf-8')
    msg['From'].append('<%s>' % sender, 'us-ascii')
    msg['To'] = Header(to_name, 'utf-8')
    msg['To'].append('<%s>' % to_addr, 'us-ascii')
    print vericode

    return None
    # try:
    #     s = smtplib.SMTP('localhost')
    #     s.sendmail(sender, [to_addr], msg.as_string())
    #     return None
    # except smtplib.SMTPException as e:
    #     return str(e)
