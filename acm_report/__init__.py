from flask import Flask
import acm_report.database as db
import acm_report.settings as settings

app = Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.db_session.remove()
