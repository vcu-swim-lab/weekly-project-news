# This file cleans the database by removing outdated or unnecessary information
# It deletes stale issues and pull requests that are no longer relevant
# It also removes repositories and other entries that are no longer active/needed
# The purpose is to keep the database lean and up to date

from github import Github
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from datetime import datetime
import logging
from sqlalchemy import create_engine
import time
from parse_github_data import *

load_dotenv()
API_KEYS = os.environ['GITHUB_API_KEYS'].split(' ')
print(API_KEYS)
current_key_index = 0
headers = {'Authorization': f'token {API_KEYS[current_key_index]}'}
g = Github(API_KEYS[current_key_index])

# Set up logging to file
logging.basicConfig(
    filename='clean-db.log',
    filemode='a',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)

def delete_element(session, obj_id, table, id='id', name='repository_full_name'):
    try:
        obj = session.query(table).filter(getattr(table, id) == obj_id).first()

        if obj:
            session.delete(obj)
            session.commit()
            logging.info(f"{table} {obj_id} deleted from {name}")
        else:
            logging.info(f"{table} {obj_id} does not exist in {name}")
    except Exception as e:
        session.rollback()
        logging.error(f"Error deleting {table} {obj_id} in {name}: {e}")

# Handles the datetime formatting issues
def handle_datetime(datetime_str):
    if datetime_str:
        return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')
    return None

# CLEAN ALL DATA
def clean_all_data(session, repo_name, one_week_ago):
    issues = get_issues(repo_name, one_week_ago)
    issue_ids = {issue['id'] for issue in issues}
    pull_ids = {issue['id'] for issue in issues if 'pull' in issue['html_url']}

    # Clean issues
    db_issues = session.query(Issue).filter(Issue.repository_full_name == repo_name).all()
    for db_issue in db_issues:
        if db_issue.id not in issue_ids:
            delete_element(session, db_issue.id, Issue, name=repo_name)

    # Clean pull requests
    db_pulls = session.query(PullRequest).filter(PullRequest.repository_full_name == repo_name).all()
    for db_pull in db_pulls:
        if db_pull.id not in pull_ids:
            delete_element(session, db_pull.id, PullRequest, name=repo_name)

    # Clean issue comments
    db_issue_comments = session.query(IssueComment).all()
    for comment in db_issue_comments:
        if comment.issue_id not in issue_ids:
            delete_element(session, comment.id, IssueComment, name=repo_name)

    # Clean pull request comments
    db_pr_comments = session.query(PullRequestComment).all()
    for comment in db_pr_comments:
        if comment.pull_request_id not in pull_ids:
            delete_element(session, comment.id, PullRequestComment, name=repo_name)

    logging.info(f"Finished cleaning data for {repo_name}")

    

# Main
if __name__ == '__main__':
    # Measure the time it takes for every function to execute. 
    start_time = time.time()
    
    # Create SQLAlchemy engine and session
    logging.getLogger('sqlalchemy').disabled = True
    engine = create_engine('sqlite:///github.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Time variables
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Making a set to keep track of processed repos to save time
    processed_repos = set()
    
    # Get a list of repos in the database
    repo_list = [r[0] for r in session.query(Repository.full_name).all()]

    # Loop through each and clean
    for repo_name in repo_list:

        # Skip repos that have already been processed
        if repo_name in processed_repos:
            continue

        repo = g.get_repo(repo_name)
        
        clean_all_data(session, repo_name, one_week_ago)

        processed_repos.add(repo_name)
        
    # Check how long the function takes to run and print result
    elapsed_time = time.time() - start_time
    if (elapsed_time >= 60):
        logging.info("This entire program took {:.2f} minutes to run".format(elapsed_time/60))
    else:
        logging.info("This entire program took {:.2f} seconds to run".format(elapsed_time))
