from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from .user import User
from .label import Label
from .repository import Repository

class Issue(Base):
    __tablename__ = 'issues'
    
    id = Column(Integer, primary_key=True)
    url = Column(String)
    comments_url = Column(String)
    html_url = Column(String)
    number = Column(Integer, nullable=False)
    state = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text)
    locked = Column(Boolean)
    active_lock_reason = Column(String)
    comments = Column(Integer)
    closed_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    user_login = Column(String)
    repository_full_name = Column(String)

    labels = relationship("Label", secondary="issue_labels")

    def __repr__(self):
        return f"<Issue(title={self.title}, state={self.state})>"

class IssueLabel(Base):
    __tablename__ = 'issue_labels'
    issue_id = Column(Integer, ForeignKey('issues.id'), primary_key=True)
    label_name = Column(Integer, ForeignKey('labels.name'), primary_key=True)

class IssueComment(Base):
    __tablename__ = 'issue_comments'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    html_url = Column(String)
    body = Column(Text)
    user_login = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    repository_full_name = Column(String)

    issue_id = Column(Integer, ForeignKey('issues.id'))
