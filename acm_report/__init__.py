from flask import Flask
import acm_report.database as db
import acm_report.settings as settings
import acm_report.utils as utils

app = Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY
app.jinja_env.filters['format_from_utc'] = utils.format_from_utc


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.db_session.remove()
