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



# def get_issues(repo_owner, repo_name, limit):
#     issues_array = []
#     page = 1

#     while len(issues_array) < limit:
#         url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
#         params = {
#             'state': 'all',
#             'page': page,
#             'per_page': 100
#         }

#         response = requests.get(url, headers=headers, params=params)
#         print(response)
#         if response.status_code != 200:
#             raise Exception(f"Failed to fetch issues: {response.status_code}")

#         page_issues = response.json()
#         if not page_issues:
#             break
        
#         for issue in page_issues:
#             if "[bot]" not in issue['user']['login'].lower() and "bot" not in issue['user']['login'].lower():
#                 issues_array.append(issue)

#         issues_array.extend(page_issues)
#         page += 1

#     return issues_array


def get_issues(g, repo_owner, repo_name, limit):
    # Get the repository
    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    
    issues_array = []
    issues = repo.get_issues(state='all')
    
    for issue in issues:
        if "[bot]" not in issue.user.login.lower() and "bot" not in issue.user.login.lower():
            issues_array.append(issue)
        if len(issues_array) >= limit:
            break

    return issues_array

# API call to get the issue comments
def get_issue_comments(repo_owner, repo_name, issue_number):
    comments = []
    page = 1
    
    while True:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments"
        params = {
            'page': page,
            'per_page': 100
        }

        response = requests.get(url, headers=headers, params=params)
        print(response)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issue comments: {response.status_code}")

        page_comments = response.json()
        if not page_comments:
            break

        comments.extend(page_comments)
        page += 1
    return comments


# API call definition for commits
def get_commits(repo_owner, repo_name, limit):
    commits = []
    page = 1
    
    while len(commits) < limit:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
        params = {
            'state': 'all',
            'page': page,
            'per_page': 100
        }

        response = requests.get(url, headers=headers, params=params)
        print(response)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues: {response.status_code}")

        page_commits = response.json()
        if not page_commits:
            break

        commits.extend(page_commits)
        page += 1
    return commits

# API call to get the commit comments
def get_commit_comments(repo_owner, repo_name, sha):
    comments = []
    page = 1
    
    while True:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{sha}/comments"
        params = {
            'page': page,
            'per_page': 100
        }

        response = requests.get(url, headers=headers, params=params)
        print(response)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issue comments: {response.status_code}")

        page_comments = response.json()
        if not page_comments:
            break

        comments.extend(page_comments)
        page += 1
    return comments


# API call to get pull requests
def get_pulls(repo_owner, repo_name, limit):
    pulls = []
    page = 1
    
    while len(pulls) < limit:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
        params = {
            'state': 'all',
            'page': page,
            'per_page': 100
        }

        response = requests.get(url, headers=headers, params=params)
        print(response)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues: {response.status_code}")

        page_pulls = response.json()
        if not page_pulls:
            break

        pulls.extend(page_pulls)
        page += 1
    return pulls
    
# API call to get the pull request comments
def get_pr_comments(repo_owner, repo_name, number):
    comments = []
    page = 1
    
    while True:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{number}/comments"
        params = {
            'page': page,
            'per_page': 100
        }

        response = requests.get(url, headers=headers, params=params)
        print(response)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issue comments: {response.status_code}")

        page_comments = response.json()
        if not page_comments:
            break

        comments.extend(page_comments)
        page += 1
    return comments


def insert_user(data): 
    repository_fields = {column.name for column in User.__table__.columns}
    filtered_data = {key: value for key, value in data.items() if key in repository_fields}

    # Create and add the repository to the session
    new_user = User(**filtered_data)
    session.add(new_user)
    session.commit()



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

    # Handle labels
    labels = []
    for label in issue.labels:
        label_obj = session.query(Label).filter_by(name=label.name).first()
        if not label_obj:
            label_obj = Label(name=label.name)
            session.add(label_obj)
            session.commit()
        labels.append(label_obj)
    filtered_data['labels'] = labels
    
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
    
# # ISSUES 1: INSERT ISSUE DATA
# def insert_issue(data):
#     # Extract only the fields that exist in the Issue model
#     issue_fields = {column.name for column in Issue.__table__.columns}
#     filtered_data = {key: value for key, value in data.items() if key in issue_fields}

#     if session.query(Issue).filter_by(id=filtered_data['id']).first() is not None:
#         print("Already Exists!")
#         return

#     if 'user' in data:
#         user_data = data['user']
#         user = session.query(User).filter_by(login=user_data['login']).first()
#         if not user:
#             insert_user(user_data)
#         user = session.query(User).filter_by(login=user_data['login']).first()
#         filtered_data['user_login'] = user.login

#     # Handle labels
#     if 'labels' in data:
#         labels_data = data['labels']
#         labels = []
#         for label_data in labels_data:
#             label = session.query(Label).filter_by(name=label_data['name']).first()
#             if not label:
#                 label = Label(name=label_data['name'],)
#                 session.add(label)
#                 session.commit()
#             labels.append(label)
#         filtered_data['labels'] = labels
        
#     # Retreive the repo name and insert into database
#     repo_name = get_repo_name(data['html_url'])
#     if repo_name is not None:
#         filtered_data['repository_full_name'] = repo_name
#     else:
#         filtered_data['repository_full_name'] = get_repo_name(data['url'])
    
#     # Convert datetime fields
#     datetime_fields = ['created_at', 'updated_at', 'closed_at']
#     for field in datetime_fields:
#         if field in filtered_data:
#             if filtered_data[field] is None:
#                 filtered_data[field] = None
#             else:
#                 filtered_data[field] = datetime.strptime(filtered_data[field], "%Y-%m-%dT%H:%M:%SZ")

#     # Create and add the issue to the session
#     new_issue = Issue(**filtered_data)
#     session.add(new_issue)
#     session.commit()
    
# ISSUES 2: ISSUE COMMENTS
def insert_issue_comment(data):
    # Extract only the fields that exist in the IssueComment model
    comment_fields = {column.name for column in IssueComment.__table__.columns}
    filtered_comment_data = {key: value for key, value in data.items() if key in comment_fields}

    # Handle user data in the comment
    if 'user' in data:
        user_data = data['user']
        user = session.query(User).filter_by(login=user_data['login']).first()
        if not user:
            user = insert_user(user_data)
            if not user:
                print(f"Failed to insert or retrieve user: {user_data}")
                return
        filtered_comment_data['user_login'] = user.login

    # Convert datetime fields
    comment_datetime_fields = ['created_at', 'updated_at']
    for field in comment_datetime_fields:
        if field in filtered_comment_data and filtered_comment_data[field] is not None:
            filtered_comment_data[field] = datetime.strptime(filtered_comment_data[field], "%Y-%m-%dT%H:%M:%SZ")

    # Assign the issue_id to the comment
    filtered_comment_data['issue_id'] = data['id']
    
    # Retreive the repo name and insert into database
    repo_name = get_repo_name(data['html_url'])
    if repo_name is not None:
        filtered_comment_data['repository_full_name'] = repo_name
    else:
        filtered_comment_data['repository_full_name'] = get_repo_name(data['url'])
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
    filtered_data = {key: value for key, value in data.items() if key in pull_fields}

    if session.query(PullRequest).filter_by(id=filtered_data['id']).first() is not None:
        print("Already Exists!")
        return

    # Handle nested user object
    if 'user' in data:
        user_data = data['user']
        user = session.query(User).filter_by(login=user_data['login']).first()
        if not user:
            insert_user(user_data)
        user = session.query(User).filter_by(login=user_data['login']).first()
        filtered_data['user_login'] = user.login
    
    # Retreive the repo name and insert into database
    repo_name = get_repo_name(data['html_url'])
    if repo_name is not None:
        filtered_data['repository_full_name'] = repo_name
    else:
        filtered_data['repository_full_name'] = get_repo_name(data['url'])
        

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
    
# PRS 2: INSERT PR COMMENT
def insert_pr_comment(data):
    comment_fields = {column.name for column in PullRequestComment.__table__.columns}
    filtered_comment_data = {key: value for key, value in data.items() if key in comment_fields}

    if 'user' in data:
        user_data = data['user']
        user = session.query(User).filter_by(login=user_data['login']).first()
        if not user:
            user = insert_user(user_data)
            if not user:
                print(f"Failed to insert or retrieve user: {user_data}")
                return
        filtered_comment_data['user_login'] = user.login

    comment_datetime_fields = ['created_at', 'updated_at']
    for field in comment_datetime_fields:
        if field in filtered_comment_data and filtered_comment_data[field] is not None:
            filtered_comment_data[field] = datetime.strptime(filtered_comment_data[field], "%Y-%m-%dT%H:%M:%SZ")

    filtered_comment_data['pull_request_id'] = data['pull_request_id']
    
    # Retreive the repo name and insert into database
    repo_name = get_repo_name(data['html_url'])
    if repo_name is not None:
        filtered_comment_data['repository_full_name'] = repo_name
    else:
        filtered_comment_data['repository_full_name'] = get_repo_name(data['url'])

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
    filtered_data = {key: value for key, value in data.items() if key in commit_fields}

    # Check if the commit already exists in the database
    if session.query(Commit).filter_by(sha=filtered_data['sha']).first() is not None:
        print("Already Exists!")
        return
    
    # Handle nested committer object
    if 'committer' in data:
        committer_data = data['committer']
        committer = session.query(User).filter(
            (User.login == committer_data.get('login')) |
            (User.name == committer_data.get('name'))
        ).first()
        if not committer:
            insert_user(committer_data)
        filtered_data['committer_login'] = committer.login
        filtered_data['committer_name'] = committer.name

    # Convert datetime fields
    datetime_fields = ['committer_date']
    for field in datetime_fields:
        if field in filtered_data:
            filtered_data[field] = datetime.strptime(filtered_data[field], "%Y-%m-%dT%H:%M:%SZ")
            
            
     # Add commit date and message
    filtered_data['commit_message'] = data.get('commit').get('message')
    filtered_data['committer_date'] = datetime.strptime(data.get('commit').get('committer').get('date'), "%Y-%m-%dT%H:%M:%SZ")
    
    # Add commit_url, commit_comment_count, and repository_full_name
    filtered_data['commit_url'] = data.get('html_url')
    filtered_data['commit_comment_count'] = data.get('commit').get('comment_count')
    
    # Retreive the repo name and insert into database
    repo_name = get_repo_name(data['html_url'])
    if repo_name is not None:
        filtered_data['repository_full_name'] = repo_name
    else:
        filtered_data['repository_full_name'] = get_repo_name(data['url'])
            
    new_commit = Commit(**filtered_data)
    session.add(new_commit)
    session.commit()
    
# COMMITS 2: INSERT COMMIT COMMENT
def insert_commit_comment(data):
    comment_fields = {column.name for column in CommitComment.__table__.columns}
    filtered_comment_data = {key: value for key, value in data.items() if key in comment_fields}

    if 'user' in data:
        user_data = data['user']
        user = session.query(User).filter_by(login=user_data['login']).first()
        if not user:
            user = insert_user(user_data)
            if not user:
                print(f"Failed to insert or retrieve user: {user_data}")
                return
        filtered_comment_data['user_login'] = user.login

    comment_datetime_fields = ['created_at', 'updated_at']
    for field in comment_datetime_fields:
        if field in filtered_comment_data and filtered_comment_data[field] is not None:
            filtered_comment_data[field] = datetime.strptime(filtered_comment_data[field], "%Y-%m-%dT%H:%M:%SZ")

    filtered_comment_data['commit_id'] = data['commit_id']
    
    # Retreive the repo name and insert into database
    repo_name = get_repo_name(data['html_url'])
    if repo_name is not None:
        filtered_comment_data['repository_full_name'] = repo_name
    else:
        filtered_comment_data['repository_full_name'] = get_repo_name(data['url'])

    try:
        new_comment = CommitComment(**filtered_comment_data)
        session.add(new_comment)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError: {e}")


if __name__ == '__main__':
    g = Github(os.environ['GITHUB_API_KEY'])
    
    # Define the limit for API calls
    limit = 100
    
    # Testing code
    owner = 'monicahq'
    repo = 'monica'
    
    repo_data = get_a_repository(owner, repo)
    insert_repository(repo_data)
    
    issues = get_issues(g, owner, repo, limit)
    for issue in issues:
        insert_issue(issue)
    
    
    # Define owners and repos arrays
    owners = ['cnovalski1', 'monicahq', 'danny-avila', 'tensorflow']
    repos = ['APIexample', 'monica', 'LibreChat', 'tensorflow']

    
    # for owner, repo in zip(owners, repos):
    # # Process repository data
    #     repo_data = get_a_repository(owner, repo)
    #     insert_repository(repo_data)

    #     # Process issues and comments
    #     issues = get_issues(owner, repo, limit)
    #     for issue in issues:
    #         if 'pull_request' in issue.keys():
    #             insert_pull_request(issue)
    #         else:
    #             insert_issue(issue)

    #         # Insert comments for each issue
    #         issue_comments = get_issue_comments(owner, repo, issue['number'])
    #         for comment in issue_comments:
    #             insert_issue_comment(comment)

    #     # Process pull requests and comments
    #     pulls = get_pulls(owner, repo, limit)
    #     for pr in pulls:
    #         insert_pull_request(pr)

    #         try:
    #             pr_comments = get_pr_comments(owner, repo, pr['number'])
    #             for comment in pr_comments:
    #                 insert_pr_comment(comment)
    #         except Exception as e:
    #             print(f"Error fetching comments for pull request {pr['id']}: {e}")

    #     # Process commits and comments
    #     commits = get_commits(owner, repo, limit)
    #     for commit in commits:
    #         insert_commit(commit)

    #         # Insert comments for each commit
    #         commit_comments = get_commit_comments(owner, repo, commit['sha'])
    #         for comment in commit_comments:
    #             insert_commit_comment(comment)
    
