from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import requests 
from sqlalchemy import create_engine
import logging
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from github import Github
from datetime import datetime, timedelta, timezone
import time
import logging
import os
import sys

# Change path to import tables and anything else
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from tables.commit import Commit


# Create the engine/test db
engine = create_engine('sqlite:///test.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
