from flask import Flask
import datetime
import acm_report.models as models
import acm_report.database as db
import acm_report.settings as settings
import acm_report.utils as utils

app = Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY
app.jinja_env.filters['format_from_utc'] = utils.format_from_utc
app.jinja_env.filters['nl2p'] = utils.nl2p
app.jinja_env.globals.update(semester_name=utils.semester_name)
app.jinja_env.globals.update(datetime=datetime.datetime)
app.jinja_env.globals.update(len=len)
app.jinja_env.globals.update(max=max)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.db_session.remove()
