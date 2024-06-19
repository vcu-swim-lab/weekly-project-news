from sqlalchemy import Column, Integer, String, Text, Boolean
from .base import Base

class Label(Base):
    __tablename__ = 'labels'
    
    name = Column(String, primary_key=True)

    def __repr__(self):
        return f"<Label(name={self.name})>"
