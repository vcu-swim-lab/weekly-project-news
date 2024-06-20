from sqlalchemy.orm import sessionmaker
from tables.base import Base, engine
from tables.repository import Repository, RepositoryAuthor
from tables.issue import Issue, IssueLabel, IssueComment
from tables.pull_request import PullRequest, PullRequestLabel, PullRequestComment
from tables.commit import Commit, CommitComment
from tables.label import Label
from tables.user import User
from datetime import datetime  # Import datetime
import json
import requests 
import os 

# Create all tables
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a session
session = Session()

GITHUB_API_KEY = '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'
headers = {'Authorization': f'token {GITHUB_API_KEY}'}


def get_a_repository(owner, repo):
    url = f'https://api.github.com/repos/{owner}/{repo}'
    print(url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repo_info = response.json()
        return repo_info
    else:
        print(f'Failed to fetch repository information: {response.status_code}')



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

owner = 'octocat'
repo = 'Hello-World'
repo_data = get_a_repository(owner, repo)
insert_repository(repo_data)

owner = 'cnovalski1'
repo = 'APIexample'
repo_data = get_a_repository(owner, repo)
insert_repository(repo_data)

owner = 'danny-avila'
repo = 'LibreChat'
repo_data = get_a_repository(owner, repo)
insert_repository(repo_data)


def get_issues(repo_owner, repo_name):
    issues_array = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
        params = {
            'state': 'all',
            'page': page,
            'per_page': 100
        }

        response = requests.get(url, headers=headers, params=params)
        print(response)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues: {response.status_code}")

        page_issues = response.json()
        if not page_issues:
            break

        issues_array.extend(page_issues)
        page += 1

    return issues_array


def insert_user(data): 
    repository_fields = {column.name for column in User.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in repository_fields}

    # Create and add the repository to the session
    new_user = User(**filtered_data)
    session.add(new_user)
    session.commit()


# Define a function to load issue data from a JSON file
def insert_issue(data):
    # Extract only the fields that exist in the Issue model
    issue_fields = {column.name for column in Issue.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in issue_fields}

    if session.query(Issue).filter_by(id=filtered_data['id']).first() is not None:
        print("Already Exists!")
        return

    if 'user' in data:
        user_data = data['user']
        user = session.query(User).filter_by(login=user_data['login']).first()
        if not user:
            insert_user(user_data)
        user = session.query(User).filter_by(login=user_data['login']).first()
        filtered_data['user_login'] = user.login

    if 'repository_url' in data:
        repository = session.query(Repository).filter_by(url=data['repository_url']).first()
        filtered_data['repository_full_name'] = repository.full_name


    if 'labels' in data:
        labels_data = data['labels']
        labels = []
        for label_data in labels_data:
            label = session.query(Label).filter_by(name=label_data['name']).first()
            if not label:
                label = Label(name=label_data['name'],)
                session.add(label)
                session.commit()
            labels.append(label)
        filtered_data['labels'] = labels

    # Convert datetime fields
    datetime_fields = ['created_at', 'updated_at', 'closed_at']
    for field in datetime_fields:
        if field in filtered_data:
            if filtered_data[field] is None:
                filtered_data[field] = None
            else:
                filtered_data[field] = datetime.strptime(filtered_data[field], "%Y-%m-%dT%H:%M:%SZ")

    # Create and add the issue to the session
    new_issue = Issue(**filtered_data)
    session.add(new_issue)
    session.commit()


def insert_pull_request(data):
    pull_fields = {column.name for column in PullRequest.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in pull_fields}

    # Handle nested user object
    if 'user' in data:
        user_data = data['user']
        user = session.query(User).filter_by(login=user_data['login']).first()
        if not user:
            insert_user(user_data)
        user = session.query(User).filter_by(login=user_data['login']).first()
        filtered_data['user_login'] = user.login

    if 'head' in data:
        repo_data = data['head']
        repo_data = repo_data['repo']
        repository = session.query(Repository).filter_by(full_name=repo_data['full_name']).first()
        filtered_data['repository_full_name'] = repository.full_name

    # Handle labels
    if 'labels' in data:
        labels_data = data['labels']
        labels = []
        for label_data in labels_data:
            label = session.query(Label).filter_by(name=label_data['name']).first()
            if not label:
                label = Label(name=label_data['name'],)
                session.add(label)
                session.commit()
            labels.append(label)
        filtered_data['labels'] = labels

    # Convert datetime fields
    datetime_fields = ['created_at', 'updated_at', 'closed_at']
    for field in datetime_fields:
        if field in filtered_data:
            if filtered_data[field] is None:
                filtered_data[field] = None
            else:
                filtered_data[field] = datetime.strptime(filtered_data[field], "%Y-%m-%dT%H:%M:%SZ")

    new_pr = PullRequest(**filtered_data)
    session.add(new_pr)
    session.commit()


# Example usage
owner = 'cnovalski1'
repo = 'APIexample'
issues_array = get_issues(owner, repo)
for issue in issues_array:
    if 'pull_request' in issue.keys():
        insert_pull_request(issue)
    else:
        insert_issue(issue)


# Example usage
owner = 'danny-avila'
repo = 'LibreChat'
issues_array = get_issues(owner, repo)
for issue in issues_array:
    if 'pull_request' in issue.keys():
        insert_pull_request(issue)
    else:
        insert_issue(issue)
