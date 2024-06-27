from sqlalchemy import Column, Integer, String, Boolean
from .base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    login = Column(String, nullable=False, unique=True)
    url = Column(String)
    html_url = Column(String)
    name = Column(String)

    def __repr__(self):
        return f"<User(login={self.login}, id={self.id})>"
