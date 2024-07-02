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
from sqlalchemy import create_engine
import logging
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from github import Github
from datetime import datetime, timedelta, timezone
import time

load_dotenv()

# Checks the rate limit
def rate_limit_check(g):
    rate_limit = g.get_rate_limit().core
    if rate_limit.remaining < 10:  
        print("Approaching rate limit, pausing...")
        now = datetime.now(tz=timezone.utc)
        sleep_duration = max(0, (rate_limit.reset - now).total_seconds() + 10)  # adding 10 seconds buffer
        time.sleep(sleep_duration)



# Create all tables
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a session
session = Session()

GITHUB_API_KEY = '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'
headers = {'Authorization': f'token {GITHUB_API_KEY}'}

# Remove the logs for creating the database
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
engine = create_engine('sqlite:///github.db')


def get_a_repository(owner, repo):
    url = f'https://api.github.com/repos/{owner}/{repo}'
    print(url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repo_info = response.json()
        return repo_info
    else:
        print(f'Failed to fetch repository information: {response.status_code}')

# Retreives the repo name from the url
def get_repo_name(url):
    parts = url.split('/')
    if len(parts) >= 5 and parts[2] == 'github.com':
        return f"{parts[3]}/{parts[4]}" 
    return None


def insert_repository(data): 
    # Extract only the fields that exist in the Repository model
    repository_fields = {column.name for column in Repository.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in repository_fields}

    # Convert datetime fields
    datetime_fields = ['created_at', 'updated_at']
    for field in datetime_fields:
        if field in filtered_data:
            filtered_data[field] = datetime.strptime(filtered_data[field], "%Y-%m-%dT%H:%M:%SZ")
    
    if session.query(Repository).filter_by(id=filtered_data['id']).first() is not None:
        print("Already Exists!")
        return

    # Create and add the repository to the session
    new_repo = Repository(**filtered_data)
    session.add(new_repo)
    session.commit()

# Retreive issues via pygithub
def get_issues(repo, limit):
    
    issues_array = []
    issues = repo.get_issues(state='all')
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    
    for issue in issues:
        if issue.pull_request:
            continue
        elif issue.created_at < one_year_ago:
            continue
        elif 'bot' in issue.user.login.lower() or '[bot]' in issue.user.login.lower():
            continue
        
        issues_array.append(issue)
        if len(issues_array) >= limit:
            break

    return issues_array

# Retreive PRs via pygithub
def get_pull_requests(repo, limit):
    pr_array = []
    pulls = repo.get_pulls()
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

    for pr in pulls:
        if pr.created_at < one_year_ago:
            continue
        elif 'bot' in pr.user.login.lower() or '[bot]' in pr.user.login.lower():
            continue
        
        pr_array.append(pr)
        if len(pr_array) >= limit:
            break
    
    return pr_array


# API call definition for commits
def get_all_commits(repo, limit):
    commit_array = []
    commits = repo.get_commits()
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

    for commit in commits:
        if commit.commit.author.date < one_year_ago:
            continue
        elif 'bot' in commit.commit.author.name.lower() or '[bot]' in commit.commit.author.name.lower():
            continue
        
        commit_array.append(commit)
        if len(commit_array) > limit:
            break
    
    return commit_array


# Insert user into database
def insert_user(data): 
    user_fields = {column.name for column in User.__table__.columns}
    
    # Extract data from the NamedUser object
    if isinstance(data, dict):
        # Extract data from the dictionary using .get() to avoid KeyError
        user_data = {
            'id': data.get('id'),
            'login': data.get('login'),
            'url': data.get('url'),
            'html_url': data.get('html_url'),
            'name': data.get('name'),
        }
    else:
        # Assume data is a NamedUser object
        user_data = {
            'id': getattr(data, 'id', None),
            'login': getattr(data, 'login', None),
            'url': getattr(data, 'url', None),
            'html_url': getattr(data, 'html_url', None),
            'name': getattr(data, 'name', None),
        }
    
    # Filter out only the fields present in the User model
    filtered_data = {key: value for key, value in user_data.items() if key in user_fields}
    
    # Check if the user already exists
    existing_user = session.query(User).filter_by(login=filtered_data['login']).first()
    if existing_user is not None:
        return existing_user  # Return the existing user if found
    
    # Create and add the user to the session
    new_user = User(**filtered_data)
    session.add(new_user)
    session.commit()
    return new_user


# ISSUES 1: INSERT ISSUE
def insert_issue(issue):
    # Extract only the fields that exist in the Issue model
    issue_fields = {column.name for column in Issue.__table__.columns}
    
    # Extract data from the issue object
    data = {
        'id': issue.id,
        'url': issue.url,
        'comments_url': issue.comments_url,
        'html_url': issue.html_url,
        'number': issue.number,
        'state': issue.state,
        'title': issue.title,
        'body': issue.body,
        'locked': issue.locked,
        'active_lock_reason': issue.active_lock_reason,
        'comments': issue.comments,
        'closed_at': issue.closed_at.isoformat() if issue.closed_at else None,
        'created_at': issue.created_at.isoformat() if issue.created_at else None,
        'updated_at': issue.updated_at.isoformat() if issue.updated_at else None,
        'user_login': issue.user.login
    }
    
    filtered_data = {key: value for key, value in data.items() if key in issue_fields}

    if session.query(Issue).filter_by(id=filtered_data['id']).first() is not None:
        print("Already Exists!")
        return

    user_data = {'login': issue.user.login}
    user = session.query(User).filter_by(login=user_data['login']).first()
    if not user:
        insert_user(user_data)
    user = session.query(User).filter_by(login=user_data['login']).first()
    filtered_data['user_login'] = user.login
    
    # Retrieve the repo name and insert into database
    repo_name = get_repo_name(issue.html_url)
    if repo_name is not None:
        filtered_data['repository_full_name'] = repo_name
    else:
        filtered_data['repository_full_name'] = get_repo_name(issue.url)
    
    # Convert datetime fields
    datetime_fields = ['created_at', 'updated_at', 'closed_at']
    for field in datetime_fields:
        if field in filtered_data:
            if filtered_data[field] is None:
                filtered_data[field] = None
            else:
                filtered_data[field] = datetime.fromisoformat(filtered_data[field])

    # Create and add the issue to the session
    new_issue = Issue(**filtered_data)
    session.add(new_issue)
    session.commit()
    
# ISSUES 2: INSERT ISSUE COMMENT
def insert_issue_comment(comment_data, issue_id):
    # Extract only the fields that exist in the IssueComment model
    comment_fields = {column.name for column in IssueComment.__table__.columns}

    # Initialize filtered_comment_data with mandatory fields
    filtered_comment_data = {
        'id': comment_data.id,
        'url': comment_data.url,
        'html_url': comment_data.html_url,
        'body': comment_data.body,
        'user_login': comment_data.user.login,
        'created_at': comment_data.created_at,
        'updated_at': comment_data.updated_at,
        'issue_id': issue_id
    }

    # Retreive the repo name and insert into database
    repo_name = get_repo_name(comment_data.html_url)
    if repo_name is not None:
        filtered_comment_data['repository_full_name'] = repo_name
    else:
        filtered_comment_data['repository_full_name'] = get_repo_name(comment_data['url'])

    # Filter out fields not in comment_fields
    filtered_comment_data = {key: value for key, value in filtered_comment_data.items() if key in comment_fields}

    # Handle user data in the comment
    if filtered_comment_data['user_login']:
        user = session.query(User).filter_by(login=filtered_comment_data['user_login']).first()
        if not user:
            user_data = {'login': filtered_comment_data['user_login']}
            user = insert_user(user_data)
            if not user:
                print(f"Failed to insert or retrieve user: {user_data}")
                return

    # Convert datetime fields if they are not None
    comment_datetime_fields = ['created_at', 'updated_at']
    for field in comment_datetime_fields:
        if field in filtered_comment_data and filtered_comment_data[field] is not None and isinstance(filtered_comment_data[field], str):
            filtered_comment_data[field] = datetime.strptime(filtered_comment_data[field], "%Y-%m-%dT%H:%M:%SZ")
    
    try:
        # Create and add the comment to the session
        new_comment = IssueComment(**filtered_comment_data)
        session.add(new_comment)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError: {e}")



# PRS 1: INSERT PULL REQUEST
def insert_pull_request(data):
    pull_fields = {column.name for column in PullRequest.__table__.columns}
    
    # Extract data from the pull request object
    filtered_data = {
        'id': data.id,
        'url': data.url,
        'comments_url': data.comments_url,
        'html_url': data.html_url,
        'number': data.number,
        'state': data.state,
        'title': data.title,
        'body': data.body,
        'comments': data.comments,
        'created_at': data.created_at,
        'updated_at': data.updated_at,
        'closed_at': data.closed_at,
        'user_login': data.user.login if data.user else None
    }
    # Filter out only the fields present in the PullRequest model
    filtered_data = {key: value for key, value in filtered_data.items() if key in pull_fields}
    
    # Check if the pull request already exists
    if session.query(PullRequest).filter_by(id=filtered_data['id']).first() is not None:
        print("Pull Request already exists!")
        return
    
    # Handle user data
    if data.user:
        user = session.query(User).filter_by(login=data.user.login).first()
        if not user:
            insert_user(data.user)  # Passing the NamedUser object directly
        user = session.query(User).filter_by(login=data.user.login).first()
        filtered_data['user_login'] = user.login
    
    # Retrieve the repo name and insert into database
    repo_name = get_repo_name(data.html_url)
    if repo_name is not None:
        filtered_data['repository_full_name'] = repo_name
    else:
        filtered_data['repository_full_name'] = get_repo_name(data.url)

    try:
        new_pr = PullRequest(**filtered_data)
        session.add(new_pr)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError: {e}")

    
# PRS 2: INSERT PR COMMENT
def insert_pr_comment(data, pr_id):
    comment_fields = {column.name for column in PullRequestComment.__table__.columns}
    
    # Extract data from the comment object
    filtered_comment_data = {
        'id': data.id,
        'url': data.url,
        'html_url': data.html_url,
        'body': data.body,
        'created_at': data.created_at,
        'updated_at': data.updated_at,
        'pull_request_id': pr_id
        }
    
    # Handle user data
    if hasattr(data, 'user'):
        user_data = data.user
        user = session.query(User).filter_by(login=user_data.login).first()
        if not user:
            user = insert_user(user_data)
            if not user:
                print(f"Failed to insert or retrieve user: {user_data}")
                return
        filtered_comment_data['user_login'] = user.login

    # Convert datetime fields if necessary
    datetime_fields = ['created_at', 'updated_at']
    for field in datetime_fields:
        if field in filtered_comment_data and isinstance(filtered_comment_data[field], str):
            filtered_comment_data[field] = datetime.strptime(filtered_comment_data[field], "%Y-%m-%dT%H:%M:%SZ")

    # Retrieve the repo name and insert into database
    repo_name = get_repo_name(data.html_url)
    if repo_name is not None:
        filtered_comment_data['repository_full_name'] = repo_name
    else:
        filtered_comment_data['repository_full_name'] = get_repo_name(data.url)

    # Filter out only the fields present in the PullRequestComment model
    filtered_comment_data = {key: value for key, value in filtered_comment_data.items() if key in comment_fields}

    try:
        new_comment = PullRequestComment(**filtered_comment_data)
        session.add(new_comment)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError: {e}")
    


# COMMITS 1: INSERT COMMIT
def insert_commit(data):
    commit_fields = {column.name for column in Commit.__table__.columns}
    
    # Extract data from the commit object
    filtered_data = {
        'sha': data.sha,
        'url': data.url,
        'html_url': data.html_url,
        'comments_url': data.comments_url,
        'committer_login': data.commit.author if data.commit.author else None,
        'committer_date': data.commit.committer.date,
        'committer_name': data.commit.author.name,
        'commit_message': data.commit.message,
        'commit_url': data.commit.url,
    }
    
    # Filter out only the fields present in the Commit model
    filtered_data = {key: value for key, value in filtered_data.items() if key in commit_fields}
    
    # Check if the commit already exists
    if session.query(Commit).filter_by(sha=filtered_data['sha']).first() is not None:
        print("Commit already exists!")
        return
    
    # Handle user data
    if data.committer:
        user = session.query(User).filter_by(login=data.committer.login).first()
        if not user:
            insert_user({'login': data.committer.login})  # Assuming insert_user function takes a dictionary
        user = session.query(User).filter_by(login=data.committer.login).first()
        filtered_data['committer_login'] = user.login
    
    # Convert datetime fields if necessary
    if isinstance(filtered_data['committer_date'], str):
        filtered_data['committer_date'] = datetime.strptime(filtered_data['committer_date'], "%Y-%m-%dT%H:%M:%SZ")
    
    # Retrieve the repo name and insert into database
    repo_name = get_repo_name(data.html_url)
    if repo_name is not None:
        filtered_data['repository_full_name'] = repo_name
    else:
        filtered_data['repository_full_name'] = get_repo_name(data.url)
    
    try:
        new_commit = Commit(**filtered_data)
        session.add(new_commit)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError: {e}")






# TODO
# 1. Add code to go through subscribers
# 2. Make proper list of repos and owners from that data, making sure to check if the repo already exists in the list



if __name__ == '__main__':
    g = Github(os.environ['GITHUB_API_KEY'])
    
    # Define the limit for API calls
    limit = 100

    # Get owners and repos
    with open("subscribers.json", 'r') as f:
        data = json.load(f)
    
    owners = []
    repos = []
    
    for subscriber in data['results']:
        repo_name = subscriber['metadata'].get('repo_name', '')
        if repo_name and 'github.com' in repo_name:
            # ex. https://github.com/cnovalski1/APIexample
            parts = repo_name.split('/')
            if len(parts) >= 5:
                owners.append(parts[3])
                repos.append(parts[4])
    
    # Custom owners and repos for testing
    # owners = ['cnovalski1', 'monicahq', 'danny-avila', 'tensorflow']
    # repos = ['APIexample', 'monica', 'LibreChat', 'tensorflow']
    # owners = ['stevenbui44']
    # repos = ['test-vscode']
    
    for owner, repo in zip(owners, repos):
    # Process repository data
        repository = g.get_repo(f"{owner}/{repo}")
        repo_data = get_a_repository(owner, repo)
        insert_repository(repo_data)
        
        # Get issues and insert them into the database
        issues = get_issues(repository, limit)
        for issue in issues:
            insert_issue(issue)
            issue_comments = issue.get_comments()

            for comment in issue_comments:
                insert_issue_comment(comment, issue.id)

        # Get pull requests and insert them into the database
        pulls = get_pull_requests(repository, limit)
        for pr in pulls:
            insert_pull_request(pr)

            pr_comments = pr.get_comments()
            
            for comment in pr_comments:
                insert_pr_comment(comment, pr.id)

        # Get commits and insert them into the database
        commits = get_all_commits(repository, limit)
        for commit in commits:
            insert_commit(commit)