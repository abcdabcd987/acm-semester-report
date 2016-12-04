import json
from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from acm_report.database import Base, db_session

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    year = Column(Integer, nullable=False)
    stuid = Column(String, unique=True)


class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', uselist=False)
    created_at = Column(TIMESTAMP, nullable=False)


class Text(Base):
    __tablename__ = 'text'
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'))
    json = Column(Text, nullable=False)


def load_report_texts(report):
    texts = db_session.query(Text).filter(Text.report_id == report.id).order_by(Text.id.asc()).all()
    json_texts = {}
    for text in texts:
        t = json.loads(text.json)
        key = t['type']
        if key not in json_texts:
            json_texts[key] = []
        json_texts[key].append(t)
    return json_texts
