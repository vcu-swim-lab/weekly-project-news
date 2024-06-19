# models/repository.py

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Repository(Base):
    __tablename__ = 'repositories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False, unique=True)
    html_url = Column(String, nullable=False, unique=True)
    description = Column(Text)
    url = Column(String)
    forks_count = Column(Integer)
    stargazers_count = Column(Integer)
    watchers_count = Column(Integer)
    open_issues_count = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<Repository(id={self.id}, full_name={self.full_name})>"

class RepositoryAuthor(Base):
    __tablename__ = 'repository_authors'

    repository_id = Column(Integer, primary_key=True)
    author_login = Column(String, primary_key=True)
    author_association = Column(String)
    last_updated_at = Column(DateTime)
    commit_count = Column(Integer)
    issue_count = Column(Integer)
    pull_request_count = Column(Integer)

