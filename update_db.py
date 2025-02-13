from github import Github
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from datetime import datetime  # Import datetime
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

def update_attribute(session, new_id, new_data, table, column, id='id', name='repository_full_name'):
    try:
        obj = session.query(table).filter(getattr(table, id) == new_id).first()

        if not obj:
            print(f"{table} {new_id} does not exist in the database")
        elif getattr(obj, column) != new_data:
            setattr(obj, column, new_data)
            session.commit()
            print(f"{table} {new_id} {column} updated to {new_data} in {name}")
        else:
            print(f"{table} {new_id} {column} is already {new_data} in {name}")
    except Exception as e:
        session.rollback()
        print(f"Error updating {table} {column} in {name}: {e}")

# Handles the datetime formatting issues
def handle_datetime(datetime_str):
    if datetime_str:
        return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%SZ')
    return None

# UPDATE ALL DATA
def update_all_data(session, repo_name, one_week_ago):
    issues = get_issues(repo_name, one_week_ago)
    num_issues = 0
    issues_updated = 0
    pulls_updated = 0
    
    for issue in issues:
        num_issues += 1
        print(f"Processing issue {num_issues} of {len(issues)} for {repo_name}")
        
        # Check for bots
        if 'bot' in issue['user']['login'].lower() or '[bot]' in issue['user']['login'].lower():
            continue
        
        # Checks if issue is pull request and update
        if 'pull' in issue['html_url']:
            pr = issue
            pr_comments = get_pr_comments(repo_name, pr)
            num_comments = len(pr_comments)
            
            # PRS 1: Update the state of a pull request
            update_attribute(session, pr['id'], pr['state'], PullRequest, 'state')
            # PRS 2: Update the number of comments of a pull request
            update_attribute(session, pr['id'], num_comments, PullRequest, 'comments')
            # PRS 3: Update the close date of a pull request
            update_attribute(session, pr['id'], handle_datetime(pr['closed_at']), PullRequest, 'closed_at')
            # PRS 4: Update the update date of a pull request
            update_attribute(session, pr['id'], handle_datetime(pr['updated_at']), PullRequest, 'updated_at')
            # PRS 5: Update the merge date of a pull request
            update_attribute(session, pr['id'], pr['merged'], PullRequest, 'merged')
            
            for comment in pr_comments:
                # PR COMMENTS 1: Update the update date of a pull request comment
                update_attribute(session, comment['id'], handle_datetime(comment['updated_at']), PullRequestComment, 'updated_at')
            
            pulls_updated += 1
            
            if num_issues % 10 == 0:
                rate_limit_check()
            
            continue
        
        issue_comments = get_issue_comments(repo_name, issue)
        num_comments = len(issue_comments)
        
        # ISSUES 1: Update the state of an issue
        update_attribute(session, issue['id'], issue['state'], Issue, 'state')
        # ISSUES 2: Update the number of comments of an issue
        update_attribute(session, issue['id'], num_comments, Issue, 'comments')
        # ISSUES 3: Update the close date of an issue
        update_attribute(session, issue['id'], handle_datetime(issue['closed_at']), Issue, 'closed_at')
        # ISSUES 4: Update the update date of an issue
        update_attribute(session, issue['id'], handle_datetime(issue['updated_at']), Issue, 'updated_at')

        for comment in issue_comments:
            # ISSUE COMMENTS 1: Update the update date of an issue comment
            update_attribute(session, comment['id'], handle_datetime(comment['updated_at']), IssueComment, 'updated_at')
        
        issues_updated += 1
        
        # REPOSITORY 1: Update the latest_release of a repository
        # update_attribute(session, ____, ____, Repository, 'latest_release', name='full_name')
        # REPOSITORY 2: Update the release_description of a repository
        # update_attribute(session, ____, ____, Repository, 'release_description', name='full_name')
        # REPOSITORY 3: Update the release_create_date of a repository
        # update_attribute(session, ____, handle_datetime(____), Repository, 'release_create_date', name='full_name')
        # REPOSITORY 4: Update the update_date of a repository
        # update_attribute(session, ____, handle_datetime(____), Repository, 'update_date', name='full_name')
        # REPOSITORY 5: Update the open_issues_count of a repository
        # update_attribute(session, ____, num_issues - pulls_updated, Repository, 'open_issues', name='full_name')

        if num_issues % 10 == 0:
                rate_limit_check()
    
    print(f"Successfully updated {issues_updated} issues in the database for {repo_name}")
    print(f"Successfully updated {pulls_updated} pull requests in the database for {repo_name}")

    

# Main
if __name__ == '__main__':
    # Measure the time it takes for every function to execute. 
    start_time = time.time()
    
    
    # Create SQLAlchemy engine and session
    logging.getLogger('sqlalchemy').disabled = True
    logging.disable(logging.WARNING)
    engine = create_engine('sqlite:///github.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Time variables
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Making a set to keep track of processed repos to save time
    processed_repos = set()
    
    # Get a list of repos in the database
    repo_list = [r[0] for r in session.query(Repository.full_name).all()]

    # Loop through each and update
    for repo_name in repo_list:

        # Skip repos that have already been processed
        if repo_name in processed_repos:
            continue

        repo = g.get_repo(repo_name)
        
        update_all_data(session, repo_name, one_week_ago)

        processed_repos.add(repo_name)
        
    # Check how long the function takes to run and print result
    elapsed_time = time.time() - start_time
    if (elapsed_time >= 60):
        print("This entire program took {:.2f} minutes to run".format(elapsed_time/60))
    else:
        print("This entire program took {:.2f} seconds to run".format(elapsed_time))
