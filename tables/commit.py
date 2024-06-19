from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
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

    commit_message = Column(Text)
    commit_url = Column(String)
    commit_comment_count = Column(Integer)

    repository_full_name = Column(String)

    def __repr__(self):
        return f"<Commit(sha={self.sha}, url={self.url})>"
