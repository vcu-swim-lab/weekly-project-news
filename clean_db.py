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
from datetime import datetime  # Import datetime
import sys
from parse_github_data import *
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
    
    # Create SQLAlchemy engine and session
    logging.getLogger('sqlalchemy').disabled = True
    engine = create_engine('sqlite:///github.db')
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
        sorted_issues_open_date = sort_issues_open_date(session, repo_name, limit)
        sorted_issues_num_comments = sort_issues_num_comments(session, repo_name, limit)
        
        # Delete commits older than one month
        commits = session.query(Commit).filter(Commit.repository_full_name == repo_name).all()
        
        num_commits_deleted = 0
        for commit in commits:
            commit_date = commit.committer_date
            
            if commit_date < thirty_days_ago:
                delete_commit(session, commit.sha)
                num_commits_deleted += 1
        
        print(f"Deleted {num_commits_deleted} commits from the database for {repo_name}")
        
        # Delete issues
        issues = session.query(Issue).filter(Issue.repository_full_name == repo_name).all()
        
        num_issues_deleted = 0
        for issue in issues:
            create_date = issue.created_at
            update_date = issue.updated_at
            close_date = issue.closed_at
            
            # Check if the issue ID is in sorted_issues_num_comments
            found_in_num_comments = any(issue.id == item['id'] for item in sorted_issues_num_comments)
            
            # Check if the issue ID is in sorted_issues_open_date
            found_in_open_date = any(issue.id == item['id'] for item in sorted_issues_open_date)
            
            # Keep "active" issues updated within the last month
            if create_date >= thirty_days_ago or update_date >= one_week_ago:
                continue
            # Delete closed issues older than one month and issues not in either of the two lists
            elif (close_date and close_date < thirty_days_ago) or (not found_in_num_comments and not found_in_open_date) or (create_date < one_year_ago):
                delete_issue(session, issue.id)
                num_issues_deleted += 1
        
        print(f"Deleted {num_issues_deleted} issues from the database for {repo_name}")        
            
        # Delete pull requests
        num_prs_deleted = 0
        
        pull_requests = session.query(PullRequest).filter(PullRequest.repository_full_name == repo_name).all()
        for pr in pull_requests:
            # Handle timezone info
            create_date = pr.created_at
            update_date = pr.updated_at
            close_date = pr.closed_at

            # Keep "active" prs updated within the last month
            if create_date >= thirty_days_ago or update_date >= one_week_ago:
                continue
            # Delete closed prs older than a month and delete open prs older than a month and not active
            elif (close_date and close_date < thirty_days_ago) or (create_date < thirty_days_ago and update_date < one_week_ago) or (create_date < one_year_ago):
                delete_pr(session, pr.id)
                num_prs_deleted += 1
        
        print(f"Deleted {num_prs_deleted} pull requests from the database for {repo_name}") 
                
                
    # Check how long the function takes to run and print result
    elapsed_time = time.time() - start_time
    if (elapsed_time >= 60):
        print("This entire program took {:.2f} minutes to run".format(elapsed_time/60))
    else:
        print("This entire program took {:.2f} seconds to run".format(elapsed_time))
    
    
        

        