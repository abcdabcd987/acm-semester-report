from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True)
    year = db.Column(db.Integer, nullable=False)
    stuid = db.Column(db.String, unique=True)


class Form(db.Model):
    __tablename__ = 'forms'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    start_time = db.Column(db.TIMESTAMP, nullable=False)
    end_time = db.Column(db.TIMESTAMP, nullable=False)
    config_yaml = db.Column(db.Text, nullable=False)


class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False)
