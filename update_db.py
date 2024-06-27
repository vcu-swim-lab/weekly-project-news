from github import Github
from datetime import datetime, timedelta, timezone
import time
import json
import os
import requests
from dotenv import load_dotenv
import concurrent.futures
import multiprocessing
import asyncio
import aiohttp
from aiohttp import ClientSession
import aiofiles
import nest_asyncio
from sqlalchemy.orm import sessionmaker
from tables.base import Base, engine
from tables.repository import Repository, RepositoryAuthor
from tables.issue import Issue, IssueLabel, IssueComment
from tables.pull_request import PullRequest, PullRequestLabel, PullRequestComment
from tables.commit import Commit, CommitComment
from tables.label import Label
from tables.user import User
from datetime import datetime  # Import datetime
import json
import requests 
import os 
from parse_github_data import *
from sort_data import *
# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a session
session = Session()
one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

issue_data_open = get_open_issues(session, repo, one_week_ago)

def update_open_issues(session, repository_full_name, open_issues_data):
    # Retrieve the repository
    repository = session.query(Repository).filter(Repository.full_name == repository_full_name).first()

    if repository:
        # Update the "open_issues" field with the new list of open issues
        repository.open_issues_list = open_issues_data

        # Commit the changes to the database
        session.commit()
    else:
        print(f"Repository '{repository_full_name}' not found.")


update_open_issues(session, "cnovalski1/APIexample", issue_data_open)
