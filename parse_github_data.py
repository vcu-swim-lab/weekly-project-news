from sqlalchemy.orm import sessionmaker
from tables.base import Base, engine
from tables.repository import Repository
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
import random

load_dotenv()
# Load API keys from .env file
API_KEYS = os.environ['GITHUB_API_KEYS'].split(' ')
current_key_index = 0

# Initialize Github instance
g = Github(API_KEYS[current_key_index])

# Checks the rate limit
def rate_limit_check():
    rate_limit = g.get_rate_limit().core
    print(rate_limit)
    
    if rate_limit.remaining < 10:  
        # print("Approaching rate limit, pausing...")
        # now = datetime.now(tz=timezone.utc)
        # sleep_duration = max(0, (rate_limit.reset - now).total_seconds() + 10)  # adding 10 seconds buffer
        # time.sleep(sleep_duration)
        print("Approaching rate limit, switching API key...")
        switch_api_key()
        rate_limit_check()

# Function to switch API keys
def switch_api_key():
    global current_key_index, g
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    g = Github(API_KEYS[current_key_index])
    print(f"Switched to API key {current_key_index + 1}")
    return g
        

# Retreives a repository
def get_a_repository(repository, headers):
    url = f'https://api.github.com/repos/{repository}'
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
        print("Repository already exists!")
        return

    # Create and add the repository to the session
    new_repo = Repository(**filtered_data)
    session.add(new_repo)
    session.commit()

# RETREIVE ISSUES 
def get_issues(g, repo, limit, date):
    rate_limit_check()
    issues_array = []
    issues = repo.get_issues(state='all', since=date)
    
    for issue in issues:
        if issue.pull_request:
            continue
        elif issue.created_at < date:
            continue
        elif 'bot' in issue.user.login.lower() or '[bot]' in issue.user.login.lower():
            continue
        
        issues_array.append(issue)
        if len(issues_array) >= limit:
            break

    return issues_array


# RETREIVE PULL REQUESTS
def get_pull_requests(g, repo, limit, date):
    rate_limit_check()
    pr_array = []
    pulls = repo.get_pulls()

    for pr in pulls:
        if pr.created_at < date:
            continue
        elif 'bot' in pr.user.login.lower() or '[bot]' in pr.user.login.lower():
            continue
        
        pr_array.append(pr)
        if len(pr_array) >= limit:
            break
    
    return pr_array


# RETREIVE COMMITS
def get_all_commits(g, repo, limit, date):
    rate_limit_check()
    commit_array = []
    commits = repo.get_commits()

    for commit in commits:
        if commit.commit.author.date < date:
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
            'html_url': data.get('html_url'),
        }
    else:
        # Assume data is a NamedUser object
        user_data = {
            'id': getattr(data, 'id', None),
            'login': getattr(data, 'login', None),
            'html_url': getattr(data, 'html_url', None)
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
        'html_url': issue.html_url,
        'number': issue.number,
        'state': issue.state,
        'title': issue.title,
        'body': issue.body,
        'comments': issue.comments,
        'closed_at': issue.closed_at.isoformat() if issue.closed_at else None,
        'created_at': issue.created_at.isoformat() if issue.created_at else None,
        'updated_at': issue.updated_at.isoformat() if issue.updated_at else None,
        'user_login': issue.user.login
    }
    
    filtered_data = {key: value for key, value in data.items() if key in issue_fields}

    if session.query(Issue).filter_by(id=filtered_data['id']).first() is not None:
        print("Issue already exists!")
        return

    user_data = {
        'id': issue.user.id,
        'login': issue.user.login,
        'html_url': issue.user.html_url
        }
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
    
    # Check if comment already exists in the database
    if session.query(IssueComment).filter_by(id=filtered_comment_data['id']).first() is not None:
        print("Issue comment already exists!")
        return

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
        
    # Check if comment already exists in the database
    if session.query(PullRequestComment).filter_by(id=filtered_comment_data['id']).first() is not None:
        print("Pull Request Comment already exists!")
        return

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
        'html_url': data.html_url,
        'committer_login': data.commit.author if data.commit.author else None,
        'committer_date': data.commit.committer.date,
        'committer_name': data.commit.author.name,
        'commit_message': data.commit.message,
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

# Insert all repository data relative to a specific date (e.g. one week, one year, etc.)
def insert_all_data(g, repository, limit, date):
    
    issues = get_issues(g, repository, limit, date)
    for issue in issues:
        print("Inserting issue" )
        insert_issue(issue)
        
        rate_limit_check()
        issue_comments = issue.get_comments()
        
        for comment in issue_comments:
            print("Inserting issue comment")
            insert_issue_comment(comment, issue.id)

    # Get pull requests and insert them into the database
    pulls = get_pull_requests(g, repository, limit, date)
    for pr in pulls:
        insert_pull_request(pr)
        print("Inserting pull request")
        rate_limit_check()
        pr_comments = pr.get_comments()
        
        for comment in pr_comments:
            print("Inserting pull request comment")
            insert_pr_comment(comment, pr.id)
        
  
    # Get commits and insert them into the database
    commits = get_all_commits(g, repository, limit, date)
    for commit in commits:
        print("Inserting commit")
        insert_commit(commit)
        
 
# TODO Add check for rate limit if 403 error
# TODO Use get_readme to retreive and parse the readme file
# Main
if __name__ == '__main__':
    # Measure the time it takes for every function to execute. 
    start_time = time.time()
    
    # Disable logging
    logging.getLogger('sqlalchemy').disabled = True
    # Create an engine and session
    engine = create_engine('sqlite:///github.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # GitHub API key and headers
    headers = {'Authorization': f'token {API_KEYS[current_key_index]}'}
    
    
    # Datetime variables
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Define the limit for API calls
    limit = 10000

    # Get owners and repos
    with open("subscribers.json", 'r') as f:
        subscriber_data = json.load(f)
    
    # Keep a list of the subscriber repos
    subscriber_repo_list = []
    
    for subscriber in subscriber_data['results']:
        repo_name = subscriber['metadata'].get('repo_name', '')
        if repo_name and 'github.com' in repo_name:
            # ex. https://github.com/cnovalski1/APIexample
            parts = repo_name.split('/')
            if len(parts) >= 5:
                full_repo_name = f"{parts[3]}/{parts[4]}"
                subscriber_repo_list.append(full_repo_name)
                
                
    # List of the current repositories in the database
    current_repo_list = session.query(Repository.full_name).all()
    current_repo_list = [item[0] for item in current_repo_list]

    # Making a set to keep track of processed repos to save time
    processed_repos = set()
    
    # Loop through each subscriber repo and insert data
    for repo in subscriber_repo_list:

        # Skip repos that have already been processed
        if repo in processed_repos:
            continue

        repository = g.get_repo(repo)
        
        # If repo already exists in database
        if repo in current_repo_list:
            insert_all_data(g, repository, limit, one_week_ago)
        else: # Repo doesn't exist in database, so insert it
            repo_data = get_a_repository(repo, headers)
            insert_repository(repo_data)

            insert_all_data(g, repository, limit, one_year_ago)

        processed_repos.add(repo)
            
    
       # Check how long the function takes to run and print result
    elapsed_time = time.time() - start_time
    if (elapsed_time >= 60):
        print("This entire program took {:.2f} minutes to run".format(elapsed_time/60))
    else:
        print("This entire program took {:.2f} seconds to run".format(elapsed_time))
    
    
        


    
