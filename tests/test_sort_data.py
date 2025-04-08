from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import requests 
import os 
import sys
from sqlalchemy import create_engine
import logging
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from github import Github
from datetime import datetime, timedelta, timezone
import time
import logging

# Change path to import tables and anything else
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from tables.commit import Commit

# TASKS TO COMPLETE
# 1. Find way to insert data into test database using dummy repo
# 2. Save the data into a JSON file to easily change the values to test inserts/removals, etc.
# 3. Split across several testing files, like a setup file and then testing file

# TEST FORMAT
# Query database
# Assert expected result (ex. check issue ID, body, etc.)
# Compare to actual result of method


# Create the engine/test db
engine = create_engine('sqlite:///test.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Insert dummy data into database

##### RELEASE TESTS #####

# TEST GET_LATEST_RELEASE

# TEST_GET_RELEASE_DESCRIPTION

# TEST_GET_RELEASE_CREATE_DATE

##### ISSUE TESTS #####

# TEST GET_OPEN_ISSUES

# TEST GET_CLOSED_ISSUES

# TEST GET_ACTIVE_ISSUES

# TEST GET_STALE_ISSUES

# TEST GET_NUM_OPEN_ISSUES_WEEKLY

# TEST GET_NUM_CLOSED_ISSUES_WEEKLY


##### PR TESTS #####

# TEST GET_OPEN_PRS

# TEST GET_CLOSED_PRS

# TEST GET_NUM_OPEN_PRS

# TEST GET_NUM_CLOSED_PRS

##### CONTRIBUTOR TESTS #####

# TEST GET_ACTIVE_CONTRIBUTORS

##### ALL DATA TESTS ####

# TEST GET_REPO_DATA