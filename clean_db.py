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
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from tables.commit import Commit
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

# TODO
# Deletes all associated comments as well
def delete_issue(issue_id):
    return

# TODO
# Deletes all associated comments as well
def delete_pr(pr_id):
    return

# TODO
# Deletes all associated comments as well
def delete_commit(commit_id):
    return



# TODO Clean database pseudocode
# For each repository in database
# Search through issues, delete if ___
# Search through PRs, delete if ___
# Search through commits, delete if ___
