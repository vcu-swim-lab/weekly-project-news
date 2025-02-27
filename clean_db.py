from github import Github
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from tables.commit import Commit
# from tables.user import User
from datetime import datetime  # Import datetime
import sys
from parse_github_data import *
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sort_data import *

# Deletes a repository from the database
def delete_repository(session, repo_name):
    repo = session.query(Repository).filter(Repository.name == repo_name).first()

    try:
        if not repo:
            print(f"Repository {repo_name} does not exist in the database")
        else:
            session.delete(repo)
            session.commit()
            print(f"Repository {repo_name} successfully deleted from the database")
    except Exception as e:
        session.rollback()
        print(f"Unable to delete repository from database: {e}")

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
            print(f"Issue {issue_id} deleted successfully from {issue.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Unable to delete issue from {issue.repository_full_name}: {e}")

# Delete all comments for a single issue
def delete_issue_comments(session, issue_id):
    comments = session.query(IssueComment).filter(IssueComment.issue_id == issue_id).all()
    
    for comment in comments:
        try:
            session.delete(comment)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Unable to delete issue comment from {comment.repository_full_name}: {e}")
    


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
            print(f"Pull Request {pr_id} deleted successfully from {pull_request.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Unable to delete pull request from {pull_request.repository_full_name}: {e}")

# Delete all comments for a single pr
def delete_pr_comments(session, pr_id):
    comments = session.query(PullRequestComment).filter(PullRequestComment.pull_request_id == pr_id)
    
    for comment in comments:
        try:
            session.delete(comment)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Unable to delete issue comment from {comment.repository_full_name}: {e}")
    


# Delete a single commit
def delete_commit(session, commit_sha):
    commit = session.query(Commit).filter(Commit.sha == commit_sha).first()
    
    try:
        if not commit:
            print(f"Commit {commit_sha} does not exist in the database")
        else:
            session.delete(commit)
            session.commit()
            print(f"Commit {commit_sha} deleted successfully from {commit.repository_full_name}")
    except Exception as e:
        session.rollback()
        print(f"Unable to delete commit from {commit.repository_full_name}: {e}")



# Main
if __name__ == '__main__':
    # Measure the time it takes for every function to execute. 
    start_time = time.time()
    
    # Disable SQLAlchemy logging
    logging.getLogger('sqlalchemy').disabled = True

    # Database file path
    db_file = 'github.db'

    # Check if the database file exists
    # If it doesn't exit without error
    if not os.path.exists(db_file):
        print(f"Database file '{db_file}' not found. Skipping execution.")
        sys.exit(0)
    else:
        # Create SQLAlchemy engine and session
        engine = create_engine(f'sqlite:///{db_file}')
        Session = sessionmaker(bind=engine)
        session = Session()
    
    # Time variables
    thirty_days_ago = datetime.now() - timedelta(days=30)
    one_week_ago = datetime.now() - timedelta(days=7)
    one_year_ago = datetime.now() - timedelta(days=365)
    
    # Define limit
    limit = 100

    # Get a list of repos in the database
    repo_list = [r[0] for r in session.query(Repository.full_name).all()]
    
    for repo_name in repo_list:
        # Lists to compare
        stale_issues = get_stale_issues(session, repo_name, one_week_ago)
        closed_prs = get_closed_prs(session, repo_name, one_week_ago)
        closed_issues = get_closed_issues(session, repo_name, one_week_ago)
        
        # Delete commits older than one month
        commits = session.query(Commit).filter(Commit.repository_full_name == repo_name).all()
        
        num_commits_deleted = 0
        for commit in commits:
            commit_date = commit.committer_date

            # Check if it's linked to a PR closed within one week ago
            closed_pr_ids = {pr['id'] for pr in closed_prs}
            
            if (commit_date < thirty_days_ago) and (commit.pull_request_id not in closed_pr_ids):
                delete_commit(session, commit.sha)
                num_commits_deleted += 1
        
        print(f"Deleted {num_commits_deleted} commits from the database for {repo_name}")
        
        # Delete issues
        issues = session.query(Issue).filter(Issue.repository_full_name == repo_name).all()
        
        num_issues_deleted = 0
        for issue in issues:
            create_date = issue.created_at
            close_date = issue.closed_at

            if (create_date is None):
                delete_issue(session, issue.id)
                num_issues_deleted += 1
                print(f"Deleted issue from {repo_name} because create_date was None")
            
            # Check if the issue ID is in stale_issues
            stale_issue_ids = {item['id'] for item in stale_issues}
            closed_issue_ids = {item['id'] for item in closed_issues}
            
            # Delete issues created more than thirty days ago and not closed within the last week, as long as they're not in stale issues
            if (create_date < thirty_days_ago) and (issue.id not in closed_issue_ids) and (issue.id not in stale_issue_ids):
                delete_issue(session, issue.id)
                num_issues_deleted += 1
        
        print(f"Deleted {num_issues_deleted} issues from the database for {repo_name}")        
            
        # Delete pull requests
        num_prs_deleted = 0
        
        pull_requests = session.query(PullRequest).filter(PullRequest.repository_full_name == repo_name).all()
        for pr in pull_requests:
            # Handle timezone info
            create_date = pr.created_at
            close_date = pr.closed_at

            if (create_date is None):
                delete_pr(session, pr.id)
                num_prs_deleted += 1
                print(f"Deleted pull request from {repo_name} because create_date was None")

            # Delete PRs older than 1 month. 
            # Condition: PRs created more than thirty days ago and not closed within the last week
            if (close_date is not None and close_date < one_week_ago):
                delete_pr(session, pr.id)
                num_prs_deleted += 1
            if (create_date < thirty_days_ago):
                delete_pr(session, pr.id)
                num_prs_deleted += 1
        
        print(f"Deleted {num_prs_deleted} pull requests from the database for {repo_name}") 
                
                
    # Check how long the function takes to run and print result
    elapsed_time = time.time() - start_time
    if (elapsed_time >= 60):
        print("This entire program took {:.2f} minutes to run".format(elapsed_time/60))
    else:
        print("This entire program took {:.2f} seconds to run".format(elapsed_time))
