from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Commit(Base):
    __tablename__ = 'commits'
    
    # id = Column(Integer, primary_key=True)
    sha = Column(String, primary_key=True)
    html_url = Column(String)

    # TODO Add commit_author
    commit_author_login = Column(String)
    commit_author_name = Column(String)
    
    committer_login = Column(String)
    committer_name = Column(String)
    
    committer_date = Column(DateTime)
    commit_message = Column(Text)
    
    repository_full_name = Column(String)
    

    def __repr__(self):
        return f"<Commit(sha={self.sha}, url={self.url})>"

    