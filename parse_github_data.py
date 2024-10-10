from sqlalchemy.orm import sessionmaker
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from tables.commit import Commit
from datetime import datetime
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
import logging

load_dotenv()
# Load API keys from .env file
API_KEYS = os.environ['GITHUB_API_KEYS'].split(' ')
print(API_KEYS)
current_key_index = 0
headers = {'Authorization': f'token {API_KEYS[current_key_index]}'}

# Initialize Github instance
g = Github(API_KEYS[current_key_index])

logging.basicConfig(filename='parse-log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Checks the rate limit
def rate_limit_check():
    global g
    try:
        rate_limit = g.get_rate_limit().core
        print(rate_limit)
        print(f"Current key number: {current_key_index + 1} of 5")
        
        if rate_limit.remaining < 50:  
            print("Approaching rate limit, switching API key...")
            switch_api_key()
            rate_limit_check()
    except Exception as e:
        logging.error("Error checking rate limit: %s", e)
        print("Error checking rate limit:", e)

# Switches API keys. When hits array limit, goes back to index 0
def switch_api_key():
    global current_key_index, g, headers
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    del headers
    headers = {'Authorization': f'token {API_KEYS[current_key_index]}'}
    print(API_KEYS[current_key_index])
    del g
    g = Github(API_KEYS[current_key_index])
    print(f"Switched to API key {current_key_index + 1}: ", API_KEYS[current_key_index])
    logging.info(f"Switched to API key {current_key_index + 1}")
    return g

# Makes sure the repo is public and the link is actually a link
def check_repo(url):
    if ".com" not in url:
        print(f"Error: {url} does not contain a link.")
        return True
    try:
        response = requests.head(url, allow_redirects=True)
        if response.status_code == 404:
            print(f"Error 404: {url} not found.")
            return True
        else:
            print(f"{url} exists. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return True

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
    try:
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
    except Exception as e:
        logging.error(f"Error inserting repository: {e}")
        session.rollback()


# RETRIEVE ISSUES
def get_issues(repo, date):
    issues_array = []
    page = 1

    while True:
        # Repo must be in form "owner/repo" for request to work
        url = f"https://api.github.com/repos/{repo}/issues"
        params = {
            'state': 'all',
            'page': page,
            'per_page': 100,
            'since': date,
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues: {response.status_code}")

        page_issues = response.json()
        if not page_issues:
            break
        

        issues_array.extend(page_issues)
        page += 1

    return issues_array

# RETRIEVE ISSUE COMMENTS
def get_issue_comments(repo, issue):
    comment_array = []
    page = 1
    issue_number = issue['number']

    while True:
        # Repo must be in form "owner/repo" for request to work
        url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
        params = {
            'page': page,
            'per_page': 100
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues: {response.status_code}")

        page_issues = response.json()
        if not page_issues:
            break
        

        comment_array.extend(page_issues)
        page += 1

    return comment_array

# RETRIEVE PULL REQUEST COMMENTS
def get_pr_comments(repo, pr):
    comment_array = []
    page = 1
    pr_number = pr['number']

    while True:
        # Repo must be in form "owner/repo" for request to work
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
        params = {
            'page': page,
            'per_page': 100
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues: {response.status_code}")

        page_issues = response.json()
        if not page_issues:
            break
        

        comment_array.extend(page_issues)
        page += 1

    return comment_array

# RETRIEVE COMMITS
def get_commits(repo, date):
    commits_array = []
    page = 1

    while True:
        # Repo must be in form "owner/repo" for request to work
        url = f"https://api.github.com/repos/{repo}/commits"
        params = {
            'page': page,
            'per_page': 100,
            'since': date
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues: {response.status_code}")

        page_issues = response.json()
        if not page_issues:
            break
        

        commits_array.extend(page_issues)
        page += 1

    return commits_array


# RETRIEVE VERSIONS
def get_versions(repo):
    versions_array = []
    page = 1

    while True:
        # Repo must be in form "owner/repo" for request to work
        url = f"https://api.github.com/repos/{repo}/tags"
        params = {
            'page': page,
            'per_page': 100,
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch issues: {response.status_code}")

        page_issues = response.json()
        if not page_issues:
            break
        
        versions_array.extend(page_issues)
        page += 1
    
    return versions_array

# ISSUES 1: INSERT ISSUE
def insert_issue(issue, repo_name):
    try:
        # Extract only the fields that exist in the Issue model
        issue_fields = {column.name for column in Issue.__table__.columns}
        filtered_data = {key: value for key, value in issue.items() if key in issue_fields}

        if session.query(Issue).filter_by(id=issue['id']).first() is not None:
            print("Issue already exists!")
            return

        # If the user login exists, set it. If not, set it equal to None
        try:
            filtered_data['user_login'] = issue['user']['login']
        except Exception as e:
            filtered_data['user_login'] = None
            print(f"User data does not exist for issue {issue['id']}: {e}")
        filtered_data['repository_full_name'] = repo_name
        
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
    except IntegrityError as e:
        logging.error(f"IntegrityError inserting issue: {e}")
        session.rollback()
    except Exception as e:
        logging.error(f"Error inserting issue: {e}")
        session.rollback()
    
# ISSUES 2: INSERT ISSUE COMMENT
def insert_issue_comment(comment_data, issue_id, repo_name):
    # Extract only the fields that exist in the IssueComment model
    comment_fields = {column.name for column in IssueComment.__table__.columns}
    filtered_comment_data = {key: value for key, value in comment_data.items() if key in comment_fields}

    # Check if comment already exists in the database
    if session.query(IssueComment).filter_by(id=comment_data['id']).first() is not None:
        print("Issue comment already exists!")
        return
        
    # Add issue ID to database and repo name
    filtered_comment_data['issue_id'] = issue_id
    filtered_comment_data['repository_full_name'] = repo_name
    
    # Try/except for user data
    try:
        filtered_comment_data['user_login'] = comment_data['user']['login']
    except Exception as e:
        filtered_comment_data['user_login'] = None
        print(f"User data does not exist for comment {comment_data['id']}: {e}")

    # Convert datetime fields if they are not None
    comment_datetime_fields = ['created_at', 'updated_at']
    for field in comment_datetime_fields:
        if field in filtered_comment_data and filtered_comment_data[field] is not None and isinstance(filtered_comment_data[field], str):
            filtered_comment_data[field] = datetime.strptime(filtered_comment_data[field], "%Y-%m-%dT%H:%M:%SZ")
    
    # Try except for inserting comment
    try:
        new_comment = IssueComment(**filtered_comment_data)
        session.add(new_comment)
        session.commit()
    except IntegrityError as e:
        logging.error(f"IntegrityError inserting issue: {e}")
        session.rollback()
    except Exception as e:
        logging.error(f"Error inserting issue: {e}")
        session.rollback()



# PRS 1: INSERT PULL REQUEST
def insert_pull_request(pull_request, repo_name):
    pull_fields = {column.name for column in PullRequest.__table__.columns}
    filtered_data = {key: value for key, value in pull_request.items() if key in pull_fields}
    
    # Check if the pull request already exists
    if session.query(PullRequest).filter_by(id=pull_request['id']).first() is not None:
        print("Pull Request already exists!")
        return
    
    # Try/except for user login
    try:
        filtered_data['user_login'] = pull_request['user']['login']
    except Exception as e:
        filtered_data['user_login'] = None
        print(f"User data does not exist for pull request {pull_request['id']}: {e}")
    filtered_data['repository_full_name'] = repo_name
    

    # Set repo name
    filtered_data['repository_full_name'] = repo_name
    
    # Convert datetime fields
    datetime_fields = ['created_at', 'updated_at', 'closed_at']
    for field in datetime_fields:
        if field in filtered_data:
            if filtered_data[field] is None:
                filtered_data[field] = None
            else:
                filtered_data[field] = datetime.fromisoformat(filtered_data[field])
    
    # Try/except for inserting pull request
    try:
        pull_fields = {column.name for column in PullRequest.__table__.columns}
        filtered_data = {key: value for key, value in pull_request.items() if key in pull_fields}
        
        # Check if the pull request already exists
        if session.query(PullRequest).filter_by(id=pull_request['id']).first() is not None:
            print("Pull Request already exists!")
            return
        
        # Try/except for user login
        try:
            filtered_data['user_login'] = pull_request['user']['login']
        except Exception as e:
            filtered_data['user_login'] = None
            print(f"User data does not exist for pull request {pull_request['id']}: {e}")
        filtered_data['repository_full_name'] = repo_name
        

        # Set repo name
        filtered_data['repository_full_name'] = repo_name
        
        # Convert datetime fields
        datetime_fields = ['created_at', 'updated_at', 'closed_at']
        for field in datetime_fields:
            if field in filtered_data:
                if filtered_data[field] is None:
                    filtered_data[field] = None
                else:
                    filtered_data[field] = datetime.fromisoformat(filtered_data[field])
        
        # Try/except for inserting pull request
        new_pr = PullRequest(**filtered_data)
        session.add(new_pr)
        session.commit()
    except IntegrityError as e:
        logging.error(f"IntegrityError inserting issue: {e}")
        session.rollback()
    except Exception as e:
        logging.error(f"Error inserting issue: {e}")
        session.rollback()

    
# PRS 2: INSERT PR COMMENT
def insert_pr_comment(comment_data, pr_id, repo_name):
    try:
        comment_fields = {column.name for column in PullRequestComment.__table__.columns}
        filtered_comment_data = {key: value for key, value in comment_data.items() if key in comment_fields}

            
        # Check if comment already exists in the database
        if session.query(PullRequestComment).filter_by(id=comment_data['id']).first() is not None:
            print("Pull Request Comment already exists!")
            return
        
        # Try/except for user data
        try:
            filtered_comment_data['user_login'] = comment_data['user']['login']
        except Exception as e:
            filtered_comment_data['user_login'] = None
            print(f"User data does not exist for comment {comment_data['id']}: {e}")
            
        # Add pr ID to database and repo name
        filtered_comment_data['pull_request_id'] = pr_id
        filtered_comment_data['repository_full_name'] = repo_name

        # Convert datetime fields if necessary
        datetime_fields = ['created_at', 'updated_at']
        for field in datetime_fields:
            if field in filtered_comment_data and isinstance(filtered_comment_data[field], str):
                filtered_comment_data[field] = datetime.strptime(filtered_comment_data[field], "%Y-%m-%dT%H:%M:%SZ")

        new_comment = PullRequestComment(**filtered_comment_data)
        session.add(new_comment)
        session.commit()
    except IntegrityError as e:
        logging.error(f"IntegrityError inserting issue: {e}")
        session.rollback()
    except Exception as e:
        logging.error(f"Error inserting issue: {e}")
        session.rollback()
    

# COMMITS 1: INSERT COMMIT
def insert_commit(commit, repo_name):
    try:
        commit_fields = {column.name for column in Commit.__table__.columns}
        filtered_data = {key: value for key, value in commit.items() if key in commit_fields}
        
        # Check if the commit already exists
        if session.query(Commit).filter_by(sha=commit['sha']).first() is not None:
            print("Commit already exists!")
            return
        
        # Try/except for committer and commit author data
        try:
            # filtered_data['commit_author_login'] = commit['author']['login'] if not None else None
            # filtered_data['commit_author_name'] = commit['commit']['author']['name'] if not None else None
            filtered_data['commit_author_login'] = commit['author']['login'] if not None else ''
            filtered_data['commit_author_name'] = commit['commit']['author']['name'] if not None else ''
            
            # filtered_data['committer_login'] = commit['committer']['login'] if not None else None
            # filtered_data['committer_name'] = commit['commit']['committer']['name'] if not None else None
            filtered_data['committer_login'] = commit['committer']['login'] if not None else ''
            filtered_data['committer_name'] = commit['commit']['committer']['name'] if not None else ''
        except Exception as e:
            print(f"Failed to fetch user data for commit {commit['sha']}: {e}")
        
        
    
        # Set repo name, committer date, and commit message
        filtered_data['repository_full_name'] = repo_name
        # filtered_data['committer_date'] = datetime.fromisoformat(commit['commit']['committer']['date'])
        # filtered_data['commit_message'] = commit['commit']['message'] if not None else None
        filtered_data['committer_date'] = datetime.fromisoformat(commit['commit']['committer']['date']) if not None else ''
        filtered_data['commit_message'] = commit['commit']['message'] if not None else ''
        
        new_commit = Commit(**filtered_data)
        session.add(new_commit)
        session.commit()
    except IntegrityError as e:
        logging.error(f"IntegrityError inserting issue: {e}")
        session.rollback()
    except Exception as e:
        logging.error(f"Error inserting issue: {e}")
        session.rollback()

# Insert all repository data relative to a specific date (e.g. one week, one year, etc.)
def insert_all_data(repo_name, date):
    
    issues = get_issues(repo_name, date)
    num_issues = 0
    issues_inserted = 0
    pulls_inserted = 0

    for issue in issues:
        num_issues += 1
        issue_create_date = datetime.fromisoformat(issue['created_at'])
        
        print(f"Processing issue {num_issues} of {len(issues)} for {repo_name}")
        # TODO Print login and check for bot
        # Check for bots
        if 'bot' in issue['user']['login'].lower() or '[bot]' in issue['user']['login'].lower():
            continue
        
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        if issue_create_date <= one_year_ago: # Make sure the issue create date are within the date
            print("Skipping issue out of date")
            continue
        
        # Checks for pull request and inserts it
        if 'pull' in issue['html_url']:
            pull_request = issue
            insert_pull_request(pull_request, repo_name)
            pulls_inserted += 1
            
            pr_comments = get_pr_comments(repo_name, pull_request)
            for comment in pr_comments:
                # Check for bots in comments
                comment_login = ""

                if comment['user']:
                    comment_login = comment['user']['login']

                if '[bot]' in comment_login.lower() or 'bot' in comment_login.lower():
                    continue
                
                insert_pr_comment(comment, pull_request['id'], repo_name)
            
            if num_issues % 10 == 0:
                rate_limit_check()
            
            continue
        
        # Insert issue
        insert_issue(issue, repo_name)
        issues_inserted += 1
        
        # Loop through comments and insert
        issue_comments = get_issue_comments(repo_name, issue) 
        for comment in issue_comments:
            # Check for bots in comments
            comment_login = ""

            if comment['user']:
                comment_login = comment['user']['login']

            if '[bot]' in comment_login.lower() or 'bot' in comment_login.lower():
                continue

            insert_issue_comment(comment, issue['id'], repo_name)

        if num_issues % 10 == 0:
            rate_limit_check()
        
    print(f"Successfully inserted {issues_inserted} issues for {repo_name} into the database for {repo_name}")
    print(f"Successfully inserted {pulls_inserted} pull requests for {repo_name} into the database for {repo_name}")
  
    # Get commits and insert them into the database
    commits = get_commits(repo_name, date)
    num_commits = 0
    commits_inserted = 0
    
    for commit in commits:
        num_commits += 1
        
        commit_date = datetime.fromisoformat(commit['commit']['committer']['date'])
        if commit_date <= date:
            print("Skipping commit out of date")
            continue
        
        try:
            commit_author_login = commit['author']['login'] if not None else ''
            commit_author_name = commit['commit']['author']['name'] if not None else ''
            committer_name = commit['commit']['committer']['name'] if not None else ''
            committer_login = commit['committer']['login'] if not None else ''
        except Exception as e:
            print(f"Failed to fetch user data for commit {commit['sha']}: {e}")
            continue
            
        # Skip bot author, NOT bot committer
        if commit_author_login and ('bot' in commit_author_login or '[bot]' in commit_author_login):
            print("Skipping bot commit")
            continue
        
        if commit_author_name and ('bot' in commit_author_name or '[bot]' in commit_author_name):
            print("Skipping bot commit")
            continue
        
        # TODO Check to make sure proper data is added for author, login, and committer data
        
        print(f"Inserting commit {num_commits} of {len(commits)} for {repo_name}")
        
        insert_commit(commit, repo_name)
        commits_inserted += 1
        
        if num_commits % 10 == 0:
            rate_limit_check()
    
    print(f"Successfully inserted {commits_inserted} commits for {repo_name} into the database for {repo_name}")
     
 
# TODO Use get_readme to retreive and parse the readme file and check release data

# Main
if __name__ == '__main__':
    # Measure the time it takes for every function to execute. 
    start_time = time.time()
    logging.info("- - - - - - - - - - - - - - - - - - - - - - - -")
    logging.info("Starting to run parse_github_data.py")
    
    # Disable logging
    logging.getLogger('sqlalchemy').disabled = True
    # Create an engine and session
    engine = create_engine('sqlite:///github.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Datetime variables
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Define the limit for API calls
    limit = 10000
    
    # Get owners and repos
    with open("subscribers.json", 'r') as f:
        subscriber_data = json.load(f)
        
    # Keep a list of the subscriber repos
    subscriber_repo_list = []

    try:
        
        for subscriber in subscriber_data['results']:
            repo_name = subscriber['metadata'].get('repo_name', '')
            if repo_name and 'github.com' in repo_name:
                # Check that the repository is public
                if check_repo(repo_name):
                    print(f"Repository is either private or does not exist.")
                    logging.warning(f"Repository {repo_name} is either private or does not exist.")
                    continue
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
            if repo in processed_repos:
                continue
            
            repo_name = repo
            logging.info(f"Starting {repo_name}")
            
            # If repo already exists in database
            if repo in current_repo_list:
                logging.info(f"Updating existing repository: {repo_name}")

                insert_all_data(repo_name, one_week_ago)
            else: # Repo doesn't exist in database, so insert it
                logging.info(f"Inserting new repository: {repo_name}")
                repo_data = get_a_repository(repo, headers)
                insert_repository(repo_data)
                insert_all_data(repo_name, one_year_ago)

            processed_repos.add(repo)
            elapsed_time = time.time() - start_time
            logging.info("Total time elapsed since the start: {:.2f} minutes".format(elapsed_time/60))
        
        # Check how long the function takes to run and print result
        elapsed_time = time.time() - start_time
        if (elapsed_time >= 60):
            print("This entire program took {:.2f} minutes to run".format(elapsed_time/60))
        else:
            print("This entire program took {:.2f} seconds to run".format(elapsed_time))
            
        logging.info(f"Elapsed time: {elapsed_time}")
        logging.info("This entire program took {:.2f} minutes to run".format(elapsed_time/60))
    
    except Exception as e:
        logging.error(f"An error occurred in the main process: {e}")
        print(f"An error occurred: {e}")
