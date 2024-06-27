from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from .user import User

class Commit(Base):
    __tablename__ = 'commits'
    
    # id = Column(Integer, primary_key=True)
    sha = Column(String, primary_key=True)
    url = Column(String)
    html_url = Column(String)
    comments_url = Column(String)

    committer_login = Column(String)
    committer_date = Column(DateTime)
    committer_name = Column(String)

    commit_message = Column(Text)
    commit_url = Column(String)
    commit_comment_count = Column(Integer)

    repository_full_name = Column(String)
    

    def __repr__(self):
        return f"<Commit(sha={self.sha}, url={self.url})>"

class CommitComment(Base):
    __tablename__ = 'commit_comments'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    html_url = Column(String)
    body = Column(Text)
    user_login = Column(String)
    author_association = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    commit_id = Column(String, primary_key=True)
    
    repository_full_name = Column(String)
    
    
    
    