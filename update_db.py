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

load_dotenv()


# ISSUES 1: Update the state of an issue
# Query database by issue ID
# Update object state
# Update in database
def update_issue_state(session, new_issue_id, new_state):
    try:
        issue = session.query(Issue).filter(Issue.id == new_issue_id).first()
        
        if not issue:
            print(f"Issue {new_issue_id} does not exist in the database")
        elif issue.state != new_state:
            issue.state = new_state
            session.commit()
            print(f"Issue {new_issue_id} state updated to {new_state}")
        else:
            print(f"Issue {new_issue_id} state is already {new_state}")
    except Exception as e:
        session.rollback()
        print(f"Error updating issue state: {e}")
    
# ISSUES 2: Update the number of comments on an issue
def update_issue_num_comments(session, new_issue_id, new_num_comments):
    try:
        issue = session.query(Issue).filter(Issue.id == new_issue_id).first()
        
        if not issue:
            print(f"Issue {new_issue_id} does not exist in the database")
        elif issue.comments != new_num_comments:
            issue.comments = new_num_comments
            session.commit()
            print(f"Issue {new_issue_id} number of comments updated to {new_num_comments}")
        else:
            print(f"Issue {new_issue_id} number of comments is already {new_num_comments}")
    except Exception as e:
        session.rollback()
        print(f"Error updating issue number of comments: {e}")

# ISSUES 3: Update the closed_at date on an issue
def update_issue_closed_at(session, new_issue_id, new_close_date):
    try:
        issue = session.query(Issue).filter(Issue.id == new_issue_id).first()
        
        if not issue:
            print(f"Issue {new_issue_id} does not exist in the database")
        elif issue.closed_at != new_close_date:
            issue.closed_at = new_close_date
            session.commit()
            print(f"Issue {new_issue_id} close date updated to {new_close_date}")
        else:
            print(f"Issue {new_issue_id} close date is already {new_close_date}")
    except Exception as e:
        session.rollback()
        print(f"Error updating issue close date: {e}")

# ISSUES 4: Update the updated_at date for an issue
def update_issue_updated_at(session, new_issue_id, new_update_date):
    try:
        issue = session.query(Issue).filter(Issue.id == new_issue_id).first()
        
        if not issue:
            print(f"Issue {new_issue_id} does not exist in the database")
        elif issue.updated_at != new_update_date:
            issue.updated_at = new_update_date
            session.commit()
            print(f"Issue {new_issue_id} update date updated to {new_update_date}")
        else:
            print(f"Issue {new_issue_id} update date is already {new_update_date}")
    except Exception as e:
        session.rollback()
        print(f"Error updating issue update date: {e}")
    

# ISSUE COMMENTS 1: Update the updated_at date for an issue comment
def update_issue_comment_updated_at(session, new_comment_id, new_update_date):
    try:
        comment = session.query(IssueComment).filter(IssueComment.id == new_comment_id).first()
        
        if not comment:
            print(f"Issue Comment {new_comment_id} does not exist in the database")
        elif comment.updated_at != new_update_date:
            comment.updated_at = new_update_date
            session.commit()
            print(f"Issue Comment {new_comment_id} update date updated to {new_update_date}")
        else:
            print(f"Issue Comment {new_comment_id} update date is already {new_update_date}")
            
    except Exception as e:
        session.rollback()
        print(f"Error updating issue comment update date: {e}")

# PRS 1: Update the state of a pull request
def update_pr_state(session, new_pr_id, new_state):
    try:
        pull_request = session.query(PullRequest).filter(PullRequest.id == new_pr_id).first()
        
        if not pull_request:
            print(f"Pull Request {new_pr_id} does not exist in the database")
        elif pull_request.state != new_state:
            pull_request.state = new_state
            session.commit()
            print(f"Pull Request {new_pr_id} state updated to {new_state}")
        else:
            print(f"Pull Request {new_pr_id} state is already {new_state}")
    except Exception as e:
        session.rollback()
        print(f"Error updating pull request state: {e}")

# PRS 2: Update the number of comments of a pull request
def update_pr_num_comments(session, new_pr_id, new_num_comments):
    try:
        pull_request = session.query(PullRequest).filter(PullRequest.id == new_pr_id).first()
        
        if not pull_request:
            print(f"Pull Request {new_pr_id} does not exist in the database")
        elif pull_request.comments != new_num_comments:
            pull_request.comments = new_num_comments
            session.commit()
            print(f"Pull Request {new_pr_id} number of comments updated to {new_num_comments}")
        else:
            print(f"Pull Request {new_pr_id} number of comments is already {new_num_comments}")
    except Exception as e:
        session.rollback()
        print(f"Error updating pull request number of comments: {e}")

# PRS 3: Update the close date of a pull request
def update_pr_closed_at(session, new_pr_id, new_close_date):
    try:
        pull_request = session.query(PullRequest).filter(PullRequest.id == new_pr_id).first()
        
        if not pull_request:
            print(f"Pull Request {new_pr_id} does not exist in the database")
        elif pull_request.closed_at != new_close_date:
            pull_request.closed_at = new_close_date
            session.commit()
            print(f"Pull Request {new_pr_id} close date updated to {new_close_date}")
        else:
            print(f"Pull Request {new_pr_id} close date is already {new_close_date}")
    except Exception as e:
        session.rollback()
        print(f"Error updating pull request close date: {e}")
        
# PRS 4: Update the update date of a pull request
def update_pr_updated_at(session, new_pr_id, new_update_date):
    try:
        pull_request = session.query(PullRequest).filter(PullRequest.id == new_pr_id).first()
        
        if not pull_request:
            print(f"Pull Request {new_pr_id} does not exist in the database")
        elif pull_request.updated_at != new_update_date:
            pull_request.updated_at = new_update_date
            session.commit()
            print(f"Pull Request {new_pr_id} update date updated to {new_update_date}")
        else:
            print(f"Pull Request {new_pr_id} update date is already {new_update_date}")
    except Exception as e:
        session.rollback()
        print(f"Error updating pull request update date: {e}")

# PR COMMENTS 1: Update the update date of a pull request comment
def update_pr_comment_updated_at(session, new_comment_id, new_update_date):
    try:
        comment = session.query(PullRequestComment).filter(PullRequestComment.id == new_comment_id).first()
        
        if not comment:
            print(f"Pull Request Comment {new_comment_id} does not exist in the database")
        elif comment.updated_at != new_update_date:
            comment.updated_at = new_update_date
            session.commit()
            print(f"Pull Request Comment {new_comment_id} update date updated to {new_update_date}")
        else:
            print(f"Pull Request Comment {new_comment_id} update date is already {new_update_date}")
            
    except Exception as e:
        session.rollback()
        print(f"Error updating issue comment update date: {e}")

# UPDATE ALL ISSUESE
def update_all_issues(repo, session, one_week_ago):
    new_issues = repo.get_issues(state='all', since=one_week_ago)
    for issue in new_issues:
        comments = issue.get_comments()
        num_comments = comments.totalCount
        
        update_issue_state(session, issue.id, issue.state)
        update_issue_num_comments(session, issue.id, num_comments)
        update_issue_closed_at(session, issue.id, issue.closed_at)
        update_issue_updated_at(session, issue.id, issue.updated_at)
        
        for comment in comments:
            update_issue_comment_updated_at(session, comment.id, comment.updated_at)
            
# UPDATE ALL PULL REQUESTS
def update_all_prs(repo, session, one_week_ago):
    new_pulls = repo.get_pulls(state='all')

    for pr in new_pulls:
        comments = pr.get_comments()
        num_comments = comments.totalCount
        
        update_pr_state(session, pr.id, pr.state)
        update_pr_num_comments(session, pr.id, num_comments)
        update_pr_closed_at(session, pr.id, pr.closed_at)
        update_pr_updated_at(session, pr.id, pr.updated_at)
        
        for comment in comments:
            update_pr_comment_updated_at(session, comment.id, comment.updated_at)



# Main
if __name__ == '__main__':
    # Create a configured "Session" class
    Session = sessionmaker(bind=engine)
    session = Session() # Create a session
    
    # Time variables
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # PyGithub
    g = Github(os.environ['GITHUB_API_KEY'])
    
    # Get a list of repos in the database
    repo_list = [r[0] for r in session.query(Repository.full_name).all()]

    # Loop through each and update
    for repo_name in repo_list:
        repo = g.get_repo(repo_name)
        
        update_all_issues(repo, session, one_week_ago)
        
        update_all_prs(repo, session, one_week_ago)
        
