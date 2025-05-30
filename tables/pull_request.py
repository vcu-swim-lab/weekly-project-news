# This file creates the PullRequest and PullRequestComment tables for the database
# They are joined using the pull_request_id column in the PullRequestComment table
# One pull request can have many comments but a comment can only have one pull request
# Also joins with the Repository table through repository_full_name

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from .base import Base
from .repository import Repository

class PullRequest(Base):
    __tablename__ = 'pull_requests'
    
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
    merged = Column(String)
    

    def __repr__(self):
        return f"<PullRequest(title={self.title}, state={self.state})>"

class PullRequestComment(Base):
    __tablename__ = 'pull_request_comments'
    id = Column(Integer, primary_key=True)
    html_url = Column(String)
    body = Column(Text)
    user_login = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    pull_request_id = Column(Integer)
    
    repository_full_name = Column(String)
