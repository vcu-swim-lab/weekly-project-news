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

owner = 'ggerganov'
repo = 'llama.cpp'
repo_data = get_a_repository(owner, repo)
insert_repository(repo_data)
