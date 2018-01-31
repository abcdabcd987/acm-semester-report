# -*- coding: utf-8 -*-

import pytz
import datetime

FLASK_SECRET_KEY = 'you can copy from: python -c "print(repr(__import__(\"os\").urandom(30)))"'
TIMEZONE = pytz.timezone('Asia/Shanghai')
WEBROOT = '/report'
