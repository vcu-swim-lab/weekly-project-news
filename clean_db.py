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

# Deletes a single issue and associated comments
def delete_issue(session, issue_id):
    # Query database for desired issue
    issue = session.query(Issue).filter(Issue.id == issue_id).first()
    
    try:
        if not issue:
            print(f"Issue {issue_id} does not exist in the database")
        else:
            delete_issue_comments(session, issue_id)
            
            session.delete(issue)  
            session.commit()
            print(f"Issue {issue_id} deleted successfully")
    except Exception as e:
        session.rollback()
        print(f"Unable to delete issue: {e}")

# Delete all comments for a single issue
def delete_issue_comments(session, issue_id):
    comments = session.query(IssueComment).filter(IssueComment.issue_id == issue_id).all()
    
    for comment in comments:
        try:
            session.delete(comment)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Unable to delete issue comment: {e}")
    


# Delete a single pull request and associated comments
def delete_pr(session, pr_id):
    # Query database for desired pull request
    pull_request = session.query(PullRequest).filter(PullRequest.id == pr_id).first()
    
    try:
        if not pull_request:
            print(f"Pull Request {pr_id} does not exist in the database")
        else:
            delete_pr_comments(session, pr_id)
            
            session.delete(pull_request)  
            session.commit()
            print(f"Pull Request {pr_id} deleted successfully")
    except Exception as e:
        session.rollback()
        print(f"Unable to delete pull request: {e}")

# Delete all comments for a single pr
def delete_pr_comments(session, pr_id):
    comments = session.query(PullRequestComment).filter(PullRequestComment.pull_request_id == pr_id)
    
    for comment in comments:
        try:
            session.delete(comment)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Unable to delete issue comment: {e}")
    


# Delete a single commit
def delete_commit(session, commit_sha):
    commit = session.query(Commit).filter(Commit.sha == commit_sha).first()
    
    try:
        if not commit:
            print(f"Commit {commit_sha} does not exist in the database")
        else:
            session.delete(commit)
            session.commit()
            print(f"Commit {commit_sha} deleted successfully")
    except Exception as e:
        session.rollback()
        print(f"Unable to delete commit: {e}")




# TODO Clean database pseudocode
# For each repository in database
# Search through issues, delete if ___
# Search through PRs, delete if ___
# Search through commits, delete if ___


# Main
if __name__ == '__main__':
    # Create a configured "Session" class
    Session = sessionmaker(bind=engine)
    session = Session() # Create a session
    
    # Time variables
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    one_month_ago = datetime.now(timezone.utc) - timedelta(days = 30)
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

    # PyGithub
    g = Github(os.environ['GITHUB_API_KEY'])
    
    # Get a list of repos in the database
    repo_list = [r[0] for r in session.query(Repository.full_name).all()]
    
    delete_commit(session, 'bde8aaaedf7fa9132c2695296b5f2b8b17bd30f3')
    
    
    # for repo_name in repo_list:
    #     # Delete commits older than one month
    #     commits = session.query(Commit).filter(Commit.repository_full_name == repo_name)
    #     for commit in commits:
    #         if commit.committer_date < one_month_ago:
    #             delete_commit(session, commit.sha)
        
    #     # Delete issues if ___
    #     issues = session.query(Issue).filter(Issue.repository_full_name == repo_name)
    #     for issue in issues:
    #         print()
            
    #     # Delete pull request if ___
    #     pull_requests = session.query(PullRequest).filter(PullRequest.repository_full_name == repo_name)
    #     for pr in pull_requests:
    #         print()
        
        