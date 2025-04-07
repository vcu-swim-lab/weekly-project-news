# Commit table for the Database
# Joins with the Repository table through repository_full_name

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Commit(Base):
    __tablename__ = 'commits'
    
    # id = Column(Integer, primary_key=True)
    sha = Column(String, primary_key=True)
    html_url = Column(String)
    commit_author_login = Column(String)
    committer_date = Column(DateTime)
    commit_message = Column(Text)
    
    repository_full_name = Column(String)

    pull_request_id = Column(Integer)
    

    def __repr__(self):
        return f"<Commit(sha={self.sha}, url={self.url})>"