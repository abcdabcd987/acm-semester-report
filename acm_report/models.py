from sqlalchemy import Column, ForeignKey, Integer, String, Enum, Text, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from acm_report.database import Base
import enum


PeerReviewType = enum.Enum('PeerReviewType', [
    'positivie',
    'negative',
    'mention',
])

PrivilegeType = enum.Enum('PrivilegeType', [
    'edit_teacher',
    'edit_course',
    'see_all_reviews',
    'assign_task',
    'grant_permission',
])

TaskRequirementType = enum.Enum('TaskRequirementType', [
    'course_review',
    'peer_review',
    'ta_review',
    'article',
])


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    stuid = Column(String, unique=True)
    name = Column(String, nullable=False)
    pinyin = Column(String, nullable=False)
    email = Column(String, unique=True)
    category = Column(String, nullable=False)
    dropped = Column(Boolean, nullable=False)


class LoginVerification(Base):
    __tablename__ = 'login_vericodes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    code = Column(String, nullable=False)
    valid = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    user = relationship("User", uselist=False)


class Privilege(Base):
    __tablename__ = 'privileges'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    privilege = Column(Enum(PrivilegeType), nullable=False)
    granted_by = Column(Integer, ForeignKey('users.id'))
    granted_at = Column(TIMESTAMP, nullable=False)


class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    update_at = Column(TIMESTAMP, nullable=False)
    text = Column(Text)


class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    course_id = Column(String, nullable=False)
    course_name = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'))


class CourseReview(Base):
    __tablename__ = 'course_reviews'
    id = Column(Integer, primary_key=True)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    text = Column(Text)


class PeerReview(Base):
    __tablename__ = 'peer_reviews'
    id = Column(Integer, primary_key=True)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reviewee_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(Enum(PeerReviewType), nullable=False)
    text = Column(Text)


class TAReview(Base):
    __tablename__ = 'ta_reviews'
    id = Column(Integer, primary_key=True)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_name = Column(String, nullable=False)
    ta_name = Column(String)
    ta_id = Column(Integer, ForeignKey('users.id'))
    text = Column(Text)


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    deadline = Column(TIMESTAMP, nullable=False)


class TaskMember(Base):
    __tablename__ = 'task_members'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)


class TaskRequirement(Base):
    __tablename__ = 'task_requirements'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    type = Column(Enum(TaskRequirementType), nullable=False)
    config = Column(String)


class ReportFragment(Base):
    __tablename__ = 'report_fragments'
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    requirement_id = Column(Integer, ForeignKey('task_requirements.id'), nullable=False)
    update_at = Column(TIMESTAMP, nullable=False)
    course_review_id = Column(Integer, ForeignKey('course_reviews.id'))
    peer_review_id = Column(Integer, ForeignKey('peer_reviews.id'))
    ta_review_id = Column(Integer, ForeignKey('ta_reviews.id'))
    article_id = Column(Integer, ForeignKey('articles.id'))


class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    finished = Column(Boolean, nullable=False)
    update_at = Column(TIMESTAMP, nullable=False)
