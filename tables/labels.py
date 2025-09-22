# This file creates the Labels table for the database
# Joins with the Repository table through repository_full_name
# Joins with the Issue table through issue_id

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from .repository import Repository

class Label(Base):
    __tablename__ = 'labels'
    
    id = Column(Integer, primary_key=True)
    url = Column(String)
    name = Column(String)
    description = Column(String)
    color = Column(String)

    # Joins
    repository_full_name = Column(String)
    issue_id = Column(Integer)
    
    def __repr__(self):
        return f"<Issue(title={self.title}, state={self.state})>"