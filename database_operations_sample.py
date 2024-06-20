from sqlalchemy.orm import sessionmaker
from tables.base import Base, engine
from tables.repository import Repository, RepositoryAuthor
from tables.issue import Issue, IssueLabel, IssueComment
from tables.pull_request import PullRequest, PullRequestLabel, PullRequestComment
from tables.commit import Commit, CommitComment
from tables.label import Label
from tables.user import User
# from tables.team import Team
from datetime import datetime  # Import datetime
import json
# Create all tables
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a session
session = Session()

def load_repository_from_json(data): 
    # Extract only the fields that exist in the Repository model
    repository_fields = {column.name for column in Repository.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in repository_fields}

    # Convert datetime fields
    datetime_fields = ['created_at', 'updated_at']
    for field in datetime_fields:
        if field in filtered_data:
            filtered_data[field] = datetime.strptime(filtered_data[field], "%Y-%m-%dT%H:%M:%SZ")
   
    # Create and add the repository to the session
    new_repo = Repository(**filtered_data)
    session.add(new_repo)
    session.commit()


def load_user_from_json(data): 
    repository_fields = {column.name for column in User.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in repository_fields}

    # Create and add the repository to the session
    new_user = User(**filtered_data)
    session.add(new_user)
    session.commit()

# Define a function to load issue data from a JSON file
def load_issue_from_json(data):
    # Extract only the fields that exist in the Issue model
    issue_fields = {column.name for column in Issue.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in issue_fields}

    if 'user' in data:
        user_data = data['user']
        user = session.query(User).filter_by(login=user_data['login']).first()
        if not user:
            load_user_from_json(user_data)
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


def load_pull_request_from_json(data):
    pull_fields = {column.name for column in PullRequest.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in pull_fields}

    # Handle nested user object
    if 'user' in data:
        user_data = data['user']
        user = session.query(User).filter_by(login=user_data['login']).first()
        if not user:
            load_user_from_json(user_data)
        user = session.query(User).filter_by(login=user_data['login']).first()
        filtered_data['user_login'] = user.login

    if 'head' in data:
        repo_data = data['head']
        repo_data = repo_data['repo']
        repository = session.query(Repository).filter_by(full_name=repo_data['full_name']).first()
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

def load_commit_from_json(data): 
    # Extract only the fields that exist in the Repository model
    commit_fields = {column.name for column in Commit.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in commit_fields}

    if 'committer' in data:
        committer_data = data['committer']
        filtered_data['committer_login'] = committer_data['login']

    if 'commit' in data:
        commit_data = data['commit']
        filtered_data['commit_message'] = commit_data['message']
        filtered_data['commit_url'] = commit_data['url']
        filtered_data['commit_comment_count'] = commit_data['comment_count']

        committer_data = commit_data['committer']
        filtered_data['committer_date'] = committer_data['date']

    # Convert datetime fields
    datetime_fields = ['committer_date']
    for field in datetime_fields:
        if field in filtered_data:
            filtered_data[field] = datetime.strptime(filtered_data[field], "%Y-%m-%dT%H:%M:%SZ")
   
    def filter_repo_full_name (commit_url):
        url_parts = commit_url.split('/')
        # Extract the relevant parts for the full name
        try:
            owner = url_parts[4]
            repo = url_parts[5]
            full_name = f"{owner}/{repo}"
            return full_name
        except IndexError:
            raise ValueError("Invalid commit URL format")

    filtered_data['repository_full_name'] = filter_repo_full_name(data['url'])

    # Create and add the repository to the session
    new_repo = Commit(**filtered_data)
    session.add(new_repo)
    session.commit()


with open('json_data/user.json', 'r') as file:
    data = json.load(file)
load_user_from_json(data)

for repo in session.query(User).all():
    print(repo)


with open('json_data/repository.json', 'r') as file:
    data = json.load(file)
load_repository_from_json(data)

for repo in session.query(Repository).all():
    print(repo)

with open('json_data/issue.json', 'r') as file:
    data = json.load(file)
load_issue_from_json(data)

for repo in session.query(Issue).all():
    print(repo)

with open('json_data/pull_request.json', 'r') as file:
    data = json.load(file)
load_pull_request_from_json(data)

for repo in session.query(PullRequest).all():
    print(repo)

with open('json_data/commit.json', 'r') as file:
    data = json.load(file)
load_commit_from_json(data)

for commit in session.query(Commit).all():
    print(commit)
