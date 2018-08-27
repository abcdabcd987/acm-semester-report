import click
import datetime
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .settings import Settings
from .models import db
from .views import mod
from . import utils, cli_actions

def create_app(config=None):
    app = Flask('acm_report', static_url_path=Settings.WEBROOT + '/static')

    app.config.from_object(Settings)
    app.config['TEMPLATES_AUTO_RELOAD'] = bool(app.debug)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = bool(app.debug)
    app.jinja_env.auto_reload = bool(app.debug)
    app.config.update(config or {})

    app.jinja_env.filters['format_from_utc'] = utils.format_from_utc
    app.jinja_env.filters['nl2p'] = utils.nl2p
    app.jinja_env.filters['markdown'] = utils.markdown_to_html5
    app.jinja_env.globals.update(WEBROOT=Settings.WEBROOT)
    app.jinja_env.globals.update(datetime=datetime.datetime)
    app.jinja_env.globals.update(len=len)
    app.jinja_env.globals.update(max=max)
    app.jinja_env.globals.update(zip=zip)

    db.init_app(app)
    csrf = CSRFProtect(app)

    app.register_blueprint(mod, url_prefix=Settings.WEBROOT)

    @app.cli.command()
    def initdb():
        db.create_all()

    @app.cli.command()
    @click.argument('filename')
    def add_users(filename):
        cli_actions.add_users(filename)

    @app.cli.command()
    @click.argument('stuid')
    @click.argument('email')
    def change_email(stuid, email):
        cli_actions.add_users(filename)

    @app.cli.command()
    @click.argument('form_id')
    def generate(form_id):
        cli_actions.generate(form_id)

    @app.cli.command()
    @click.argument('filename')
    @click.option('--debug', is_flag=True)
    def add_form(filename, debug):
        cli_actions.add_form(filename, debug)

    @app.cli.command()
    @click.argument('form_id')
    @click.argument('filename')
    @click.option('--debug', is_flag=True)
    def update_form(form_id, filename, debug):
        cli_actions.update_form(form_id, filename, debug)

    @app.cli.command()
    @click.argument('form_id')
    def hack_reviews(form_id):
        cli_actions.hack_reviews(form_id)

    return app
