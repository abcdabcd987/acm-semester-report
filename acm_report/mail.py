import smtplib
import traceback
from email.mime.text import MIMEText
from email.header import Header
from flask import current_app


def send_vericode(to_addr, to_name, vericode):
    sender = current_app.config['MAIL_FROM']
    text = current_app.config['MAIL_BODY'].format(name=to_name, vericode=vericode)
    msg = MIMEText(text, 'plain', 'utf-8')
    msg['Subject'] = Header(current_app.config['MAIL_SUBJECT'], 'utf-8')
    msg['From'] = Header(current_app.config['MAIL_FROM_NAME'], 'utf-8')
    msg['From'].append('<%s>' % sender, 'us-ascii')
    msg['To'] = Header(to_name, 'utf-8')
    msg['To'].append('<%s>' % to_addr, 'us-ascii')

    if current_app.debug:
        print('vericode', to_addr, vericode)
    else:
        try:
            s = smtplib.SMTP('localhost')
            s.sendmail(sender, [to_addr], msg.as_string())
            return None
        except:
            return traceback.format_exc()
