# models/pull_request.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from .base import Base
from .user import User
from .label import Label
from .repository import Repository

class PullRequest(Base):
    __tablename__ = 'pull_requests'
    
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
    author_association = Column(String)

    user_login = Column(String)
    repository_full_name = Column(String)

    labels = relationship("Label", secondary="pull_request_labels")
    

    def __repr__(self):
        return f"<PullRequest(title={self.title}, state={self.state})>"

class PullRequestLabel(Base):
    __tablename__ = 'pull_request_labels'
    pull_request_id = Column(Integer, ForeignKey('pull_requests.id'), primary_key=True)
    label_name = Column(Integer, ForeignKey('labels.name'), primary_key=True)

class PullRequestComment(Base):
    __tablename__ = 'pull_request_comments'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    html_url = Column(String)
    body = Column(Text)
    user_login = Column(String)
    author_association = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    pull_request_id = Column(Integer)
    
    repository_full_name = Column(String)
    

