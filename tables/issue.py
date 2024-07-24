from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from .repository import Repository

class Issue(Base):
    __tablename__ = 'issues'
    
    id = Column(Integer, primary_key=True)
    html_url = Column(String)
    number = Column(Integer, nullable=False)
    state = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text)
    comments = Column(Integer)
    closed_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    user_login = Column(String)
    repository_full_name = Column(String)
    
    def __repr__(self):
        return f"<Issue(title={self.title}, state={self.state})>"

class IssueComment(Base):
    __tablename__ = 'issue_comments'
    id = Column(Integer, primary_key=True)
    html_url = Column(String)
    body = Column(Text)
    user_login = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    repository_full_name = Column(String)

    issue_id = Column(Integer)
