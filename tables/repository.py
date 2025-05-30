# Repository table for the database
# Inserted from subscriber repository links

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Repository(Base):
    __tablename__ = 'repositories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False, unique=True)
    html_url = Column(String, nullable=False, unique=True)
    url = Column(String)
    open_issues_count = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    latest_release = Column(String)
    release_description = Column(String)
    release_create_date = Column(DateTime)
    
    def __repr__(self):
        return f"<Repository(id={self.id}, full_name={self.full_name})>"

