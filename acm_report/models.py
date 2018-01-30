from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP
from acm_report.database import Base, db_session


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    year = Column(Integer, nullable=False)
    stuid = Column(String, unique=True)


class Form(Base):
    __tablename__ = 'forms'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    config_yaml = Column(Text, nullable=False)


class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    form_id = Column(Integer, ForeignKey('forms.id'), nullable=False)
    json = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
