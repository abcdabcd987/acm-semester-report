from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from acm_report.database import Base

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
