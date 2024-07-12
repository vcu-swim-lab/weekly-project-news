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

# ISSUES 1: Update the state of an issue
def update_issue_state(session, new_issue_id, new_state):
    try:
        issue = session.query(Issue).filter(Issue.id == new_issue_id).first()
        
        if not issue:
            print(f"Issue {new_issue_id} does not exist in the database")
        elif issue.state != new_state:
            issue.state = new_state
            session.commit()
            print(f"Issue {new_issue_id} state updated to {new_state} in {issue.repository_full_name}")
        else:
            print(f"Issue {new_issue_id} state is already {new_state} in {issue.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Error updating issue state in {issue.repository_full_name}: {e}")
    
# ISSUES 2: Update the number of comments on an issue
def update_issue_num_comments(session, new_issue_id, new_num_comments):
    try:
        issue = session.query(Issue).filter(Issue.id == new_issue_id).first()
        
        if not issue:
            print(f"Issue {new_issue_id} does not exist in the database")
        elif issue.comments != new_num_comments:
            issue.comments = new_num_comments
            session.commit()
            print(f"Issue {new_issue_id} number of comments updated to {new_num_comments} in {issue.repository_full_name}")
        else:
            print(f"Issue {new_issue_id} number of comments is already {new_num_comments} in {issue.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Error updating issue number of comments in {issue.repository_full_name}: {e}")

# ISSUES 3: Update the closed_at date on an issue
def update_issue_closed_at(session, new_issue_id, new_close_date):
    try:
        issue = session.query(Issue).filter(Issue.id == new_issue_id).first()
        
        if not issue:
            print(f"Issue {new_issue_id} does not exist in the database")
        elif issue.closed_at != new_close_date:
            issue.closed_at = new_close_date
            session.commit()
            print(f"Issue {new_issue_id} close date updated to {new_close_date} in {issue.repository_full_name}")
        else:
            print(f"Issue {new_issue_id} close date is already {new_close_date} in {issue.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Error updating issue close date in {issue.repository_full_name}: {e}")

# ISSUES 4: Update the updated_at date for an issue
def update_issue_updated_at(session, new_issue_id, new_update_date):
    try:
        issue = session.query(Issue).filter(Issue.id == new_issue_id).first()
        
        if not issue:
            print(f"Issue {new_issue_id} does not exist in the database")
        elif issue.updated_at != new_update_date:
            issue.updated_at = new_update_date
            session.commit()
            print(f"Issue {new_issue_id} update date updated to {new_update_date} in {issue.repository_full_name}")
        else:
            print(f"Issue {new_issue_id} update date is already {new_update_date} in {issue.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Error updating issue update date in {issue.repository_full_name}: {e}")
    

# ISSUE COMMENTS 1: Update the updated_at date for an issue comment
def update_issue_comment_updated_at(session, new_comment_id, new_update_date):
    try:
        comment = session.query(IssueComment).filter(IssueComment.id == new_comment_id).first()
        
        if not comment:
            print(f"Issue Comment {new_comment_id} does not exist in the database")
        elif comment.updated_at != new_update_date:
            comment.updated_at = new_update_date
            session.commit()
            print(f"Issue Comment {new_comment_id} update date updated to {new_update_date} in {comment.repository_full_name}")
        else:
            print(f"Issue Comment {new_comment_id} update date is already {new_update_date} in {comment.repository_full_name}")
            
    except Exception as e:
        session.rollback()
        print(f"Error updating issue comment update date in {comment.repository_full_name}: {e}")

# PRS 1: Update the state of a pull request
def update_pr_state(session, new_pr_id, new_state):
    try:
        pull_request = session.query(PullRequest).filter(PullRequest.id == new_pr_id).first()
        
        if not pull_request:
            print(f"Pull Request {new_pr_id} does not exist in the database")
        elif pull_request.state != new_state:
            pull_request.state = new_state
            session.commit()
            print(f"Pull Request {new_pr_id} state updated to {new_state} in {pull_request.repository_full_name}")
        else:
            print(f"Pull Request {new_pr_id} state is already {new_state} in {pull_request.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Error updating pull request state in {pull_request.repository_full_name}: {e}")

# PRS 2: Update the number of comments of a pull request
def update_pr_num_comments(session, new_pr_id, new_num_comments):
    try:
        pull_request = session.query(PullRequest).filter(PullRequest.id == new_pr_id).first()
        
        if not pull_request:
            print(f"Pull Request {new_pr_id} does not exist in the database")
        elif pull_request.comments != new_num_comments:
            pull_request.comments = new_num_comments
            session.commit()
            print(f"Pull Request {new_pr_id} number of comments updated to {new_num_comments} in {pull_request.repository_full_name}")
        else:
            print(f"Pull Request {new_pr_id} number of comments is already {new_num_comments} in {pull_request.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Error updating pull request number of comments in {pull_request.repository_full_name}: {e}")

# PRS 3: Update the close date of a pull request
def update_pr_closed_at(session, new_pr_id, new_close_date):
    try:
        pull_request = session.query(PullRequest).filter(PullRequest.id == new_pr_id).first()
        
        if not pull_request:
            print(f"Pull Request {new_pr_id} does not exist in the database")
        elif pull_request.closed_at != new_close_date:
            pull_request.closed_at = new_close_date
            session.commit()
            print(f"Pull Request {new_pr_id} close date updated to {new_close_date} in {pull_request.repository_full_name}")
        else:
            print(f"Pull Request {new_pr_id} close date is already {new_close_date} in {pull_request.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Error updating pull request close date in {pull_request.repository_full_name}: {e}")
        
# PRS 4: Update the update date of a pull request
def update_pr_updated_at(session, new_pr_id, new_update_date):
    try:
        pull_request = session.query(PullRequest).filter(PullRequest.id == new_pr_id).first()
        
        if not pull_request:
            print(f"Pull Request {new_pr_id} does not exist in the database")
        elif pull_request.updated_at != new_update_date:
            pull_request.updated_at = new_update_date
            session.commit()
            print(f"Pull Request {new_pr_id} update date updated to {new_update_date} in {pull_request.repository_full_name}")
        else:
            print(f"Pull Request {new_pr_id} update date is already {new_update_date} in {pull_request.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Error updating pull request update date in {pull_request.repository_full_name}: {e}")

# PR COMMENTS 1: Update the update date of a pull request comment
def update_pr_comment_updated_at(session, new_comment_id, new_update_date):
    try:
        comment = session.query(PullRequestComment).filter(PullRequestComment.id == new_comment_id).first()
        
        if not comment:
            print(f"Pull Request Comment {new_comment_id} does not exist in the database")
        elif comment.updated_at != new_update_date:
            comment.updated_at = new_update_date
            session.commit()
            print(f"Pull Request Comment {new_comment_id} update date updated to {new_update_date} in {comment.repository_full_name}")
        else:
            print(f"Pull Request Comment {new_comment_id} update date is already {new_update_date} in {comment.repository_full_name}")
            
    except Exception as e:
        session.rollback()
        print(f"Error updating issue comment update date in {comment.repository_full_name}: {e}")

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
            
            update_pr_state(session, pr['id'], pr['state'])
            update_pr_num_comments(session, pr['id'], num_comments)
            update_pr_closed_at(session, pr['id'], handle_datetime(pr['closed_at']))
            update_pr_updated_at(session, pr['id'], handle_datetime(pr['updated_at']))
            
            for comment in pr_comments:
                update_pr_comment_updated_at(session, comment['id'], handle_datetime(comment['updated_at']))
            
            pulls_updated += 1
            
            if num_issues % 10 == 0:
                rate_limit_check()
            
            continue
        
        issue_comments = get_issue_comments(repo_name, issue)
        num_comments = len(issue_comments)
        
        update_issue_state(session, issue['id'], issue['state'])
        update_issue_num_comments(session, issue['id'], num_comments)
        update_issue_closed_at(session, issue['id'], handle_datetime(issue['closed_at']))
        update_issue_updated_at(session, issue['id'], handle_datetime(issue['updated_at']))
        
        for comment in issue_comments:
            update_issue_comment_updated_at(session, comment['id'], handle_datetime(comment['updated_at']))
        
        issues_updated += 1
        
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
    
    
        
