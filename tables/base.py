# Creates the base engine for the SQLite Database

from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine('sqlite:///github.db', echo=True)
