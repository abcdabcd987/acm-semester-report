from sqlalchemy import Column, ForeignKey, Integer, String, Enum, Text, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from acm_report.database import Base
import enum


PeerReviewType = enum.Enum('PeerReviewType', [
    'positive',
    'negative',
    'neutral',
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
    'freetext',
    'base',
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
    allow_login = Column(Boolean, nullable=False)


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


class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    course_id = Column(String, nullable=False)
    course_name = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'))


class TaskRequirement(Base):
    __tablename__ = 'task_requirements'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    type = Column(Enum(TaskRequirementType), nullable=False)
    order = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    number = Column(Integer, nullable=False)
    config = Column(Text)


class ReportFragment(Base):
    __tablename__ = 'report_fragments'
    id = Column(Integer, primary_key=True)
    review_type = Column(Enum(TaskRequirementType), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    requirement_id = Column(Integer, ForeignKey('task_requirements.id'), nullable=False)
    order = Column(Integer, nullable=False)
    update_at = Column(TIMESTAMP, nullable=False)
    report = relationship('Report', uselist=False)
    requirement = relationship('TaskRequirement', uselist=False)
    __mapper_args__ = {
        'polymorphic_identity': TaskRequirementType.base,
        'polymorphic_on': review_type,
        'with_polymorphic': '*'
    }


class FreeText(ReportFragment):
    __tablename__ = 'freetexts'
    id = Column(Integer, ForeignKey('report_fragments.id'), primary_key=True)
    text = Column(Text)
    __mapper_args__ = {
        'polymorphic_identity': TaskRequirementType.freetext,
    }


class CourseReview(ReportFragment):
    __tablename__ = 'course_reviews'
    id = Column(Integer, ForeignKey('report_fragments.id'), primary_key=True)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'))
    text = Column(Text)
    __mapper_args__ = {
        'polymorphic_identity': TaskRequirementType.course_review,
    }


class PeerReview(ReportFragment):
    __tablename__ = 'peer_reviews'
    id = Column(Integer, ForeignKey('report_fragments.id'), primary_key=True)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reviewee_id = Column(Integer, ForeignKey('users.id'))
    type = Column(Enum(PeerReviewType), nullable=False)
    text = Column(Text)
    reviewee = relationship('User', uselist=False, foreign_keys=[reviewee_id])
    __mapper_args__ = {
        'polymorphic_identity': TaskRequirementType.peer_review,
    }


class TAReview(ReportFragment):
    __tablename__ = 'ta_reviews'
    id = Column(Integer, ForeignKey('report_fragments.id'), primary_key=True)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'))
    ta_name = Column(String)
    ta_id = Column(Integer, ForeignKey('users.id'))
    text = Column(Text)
    __mapper_args__ = {
        'polymorphic_identity': TaskRequirementType.ta_review,
    }


class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    published = Column(Boolean, nullable=False)
    update_at = Column(TIMESTAMP, nullable=False)
    user = relationship('User', uselist=False)
    task = relationship('Task', uselist=False)
    fragments = relationship('ReportFragment')


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    deadline = Column(TIMESTAMP, nullable=False)
    published = Column(Boolean, nullable=False)
    users = relationship('User', secondary=Report.__table__, order_by='User.id.desc()')
    requirements = relationship('TaskRequirement', order_by='TaskRequirement.order.asc()')
