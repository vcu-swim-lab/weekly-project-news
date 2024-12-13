from github import Github
from datetime import datetime, timedelta, timezone
import time
import json
import os
import requests
from dotenv import load_dotenv
import concurrent.futures
import multiprocessing
import asyncio
import aiohttp
from aiohttp import ClientSession
from sqlalchemy.orm import sessionmaker
import os
import sys
from datetime import datetime  # Import datetime
import json
import requests 
from parse_github_data import *
from sqlalchemy import and_
from sqlalchemy_json import NestedMutableJson
from sqlalchemy import create_engine
import logging
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from tables.commit import Commit
import operator
import base64
from urllib.parse import quote


load_dotenv()

# Checks the rate limit
def rate_limit_check(g):
    rate_limit = g.get_rate_limit().core
    if rate_limit.remaining < 10:  
        print("Approaching rate limit, pausing...")
        now = datetime.now(tz=timezone.utc)
        sleep_duration = max(0, (rate_limit.reset - now).total_seconds() + 10)  # adding 10 seconds buffer
        time.sleep(sleep_duration)

# RELEASES 1: Get latest version
def get_latest_release(session, repository_full_name):
    # Get the specific repo
    latest_version = session.query(Repository.latest_release).filter(
        and_(
            Repository.full_name == repository_full_name
        )
    ).scalar()

    return latest_version if not None else None

# ISSUES 1: Gets all open issues within one_week_ago
def get_open_issues(session, one_week_ago, repository_full_name):
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name, 
            Issue.state == 'open', 
            Issue.created_at >= one_week_ago
        )
    ).all()
    
    open_issue_data = []

    # Loop through each issue
    for issue in issues:
        # Omit bots
        if "bot" in issue.user_login.lower() or "[bot]" in issue.user_login.lower():
            continue
        
        issue_data = {
        'title': issue.title,
        "body": issue.body,
        "url": issue.html_url,
        "comments": []
        }
        comments = session.query(IssueComment).filter(IssueComment.issue_id == issue.id).all()
        for comment in comments:
            issue_data["comments"].append({"body": comment.body})
        
        open_issue_data.append(issue_data)
            
    
    return open_issue_data
    
# ISSUES 2: Gets all closed issues within one_week_ago
def get_closed_issues(session, one_week_ago, repository_full_name):
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name, 
            Issue.state == 'closed', 
            Issue.closed_at >= one_week_ago
        )
    ).all()
    
    closed_issue_data = []

    for issue in issues:
        # Omit bots
        if "bot" in issue.user_login.lower() or "[bot]" in issue.user_login.lower():
            continue
        
        issue_data = {
        'title': issue.title,
        "body": issue.body,
        "url": issue.html_url,
        "comments": []
        }
        comments = session.query(IssueComment).filter(IssueComment.issue_id == issue.id).all()
        for comment in comments:
            issue_data["comments"].append({"body": comment.body})
        
        closed_issue_data.append(issue_data)
    
    return closed_issue_data

# ISSUES 3: Get list of "active" issues, which are issues commented on the most within the past week
def get_active_issues(session, one_week_ago, repository_full_name):
    # Retrieve issues and set up variables
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name, 
            Issue.state == 'open',
            Issue.comments > 0
        )
    ).all()
    
    active_issue_data = []
    
    # Iterate through each issue and select "active" issues
    for issue in issues:
        # Omit bots
        if "bot" in issue.user_login.lower() or "[bot]" in issue.user_login.lower():
            continue

        # Add necessary data to the issue data array
        issue_data = {
            "title": issue.title,
            "body": issue.body,
            "user": issue.user_login,
            "url": issue.html_url,
            "comments": [],
            "num_comments_this_week": 0 # Placeholder as 0
        }
        
        # Query comments
        comments = session.query(IssueComment).filter(IssueComment.issue_id == issue.id).all()
        num_comments_this_week = 0
        one_week_ago = one_week_ago.replace(tzinfo=None)
        for comment in comments:
            create_date = comment.created_at.replace(tzinfo=None)
            if create_date >= one_week_ago:
                num_comments_this_week += 1
            issue_data["comments"].append({"body": comment.body})
        
        issue_data["num_comments_this_week"] = num_comments_this_week
        
        active_issue_data.append(issue_data)

    # Sort the issues in order of number of comments this week
    sorted_active_issues = sorted(active_issue_data, key=lambda x: x["num_comments_this_week"], reverse=True)

    # Check if there are any active issues
    if sorted_active_issues:
        # If there are active issues, check the first one
        if sorted_active_issues[0]["num_comments_this_week"] == 0:
            return []
    else:
        # Handle the case where there are no active issues
        return []

    return sorted_active_issues[:5]


  
# ISSUES 4: Gets stale issues (not updated within 30 days)
def get_stale_issues(session, repository_full_name, limit, thirty_days_ago): 
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name, 
            Issue.state == 'open', 
            Issue.updated_at <= thirty_days_ago
        )
    ).order_by(
        Issue.created_at.asc()
    ).all()
    
    # Set up data variables
    issue_data_sorted = []
    
    # Loop through each issue
    for issue in issues:
        # Omit bots
        if "bot" in issue.user_login.lower() or "[bot]" in issue.user_login.lower():
            continue
        
        # Calculate the time open in days, hours, and minutes
        time_open = datetime.now(timezone.utc)-issue.created_at.replace(tzinfo=timezone.utc)
        days = time_open.days
        hours, remainder = divmod(time_open.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Store the issue title, time open in days, hours, and minutes, minutes open, and a link to the issue
        issue_data = {
            "title": issue.title,
            "time_open": f"{days} days, {hours:02} hours, {minutes:02} minutes",
            "body": issue.body,
            "url": issue.html_url,
            "id": issue.id
        }
        issue_data_sorted.append(issue_data) # Append to issue data for output
        
        # Break the for loop if the amount of data is large enough
        if len(issue_data) >= limit:
            break
        
    
    return issue_data_sorted

# ISSUES 5: Get number of open issues in the last week
def get_num_open_issues_weekly(weekly_open_issues):
    return len(weekly_open_issues)

# ISSUES 6: Get number of closed issues in the last week
def get_num_closed_issues_weekly(weekly_closed_issues):
    return len(weekly_closed_issues)


# PRS 1: Gets open pull requests within one_week_ago
def get_open_prs(session, one_week_ago, repository_full_name):
    # Query the database for pull requests
    pulls = session.query(PullRequest).filter(
        and_(
            PullRequest.repository_full_name == repository_full_name, 
            PullRequest.state == 'open', 
            PullRequest.created_at >= one_week_ago
        )
    ).all()
    
    # Array to store data
    open_pr_data = []
    
    # Loop through each PR
    for pr in pulls:
        # Omit bots
        if "bot" in pr.user_login.lower() or "[bot]" in pr.user_login.lower():
            continue

        pr_data = {
                "title": pr.title,
                "body": pr.body,
                "url": pr.html_url,
                "commits": []
            }
        
        # Retreive commits for pull request
        pr_commits = session.query(Commit).filter(Commit.pull_request_id == pr.id)
        
        # Loop through commits and add links to array
        for commit in pr_commits:
            commit_data = {
                "commit_message": commit.commit_message,
                "html_url": commit.html_url
            }
            pr_data["commits"].append(commit_data)

        open_pr_data.append(pr_data)
        

    return open_pr_data

# PRS 2: Gets closed pull requests within one_week_ago
def get_closed_prs(session, one_week_ago, repository_full_name):
    # Query the database for pull requests
    pulls = session.query(PullRequest).filter(
        and_(
            PullRequest.repository_full_name == repository_full_name, 
            PullRequest.state == 'closed', 
            PullRequest.closed_at >= one_week_ago
        )
    ).all()
    
    # Array to store pull request data
    closed_pr_data = []
    
    # Loop through each PR
    for pr in pulls:
        # Omit bots
        if "bot" in pr.user_login.lower() or "[bot]" in pr.user_login.lower():
            continue
        
        pr_data = {
                "title": pr.title,
                "body": pr.body,
                "url": pr.html_url,
                "commits": []
            }
        
        # Retreive commits for pull request
        pr_commits = session.query(Commit).filter(Commit.pull_request_id == pr.id)
        
        # Loop through commits and add links to array
        for commit in pr_commits:
            commit_data = {
                "commit_message": commit.commit_message,
                "html_url": commit.html_url
            }
            pr_data["commits"].append(commit_data)
            print(commit_data)
        
        closed_pr_data.append(pr_data)

    return closed_pr_data

# PRS 3: Get NUMBER of OPEN pull requests made within one_week_ago
def get_num_open_prs(pr_data_open):
    return len(pr_data_open)

# PRS 4: Get NUMBER of CLOSED pull requests made within one_week_ago
def get_num_closed_prs(pr_data_closed):
    return len(pr_data_closed)



# COMMITS 1: Gets ALL commits within one_week_ago
def get_commit_messages(session, one_week_ago, repository_full_name):
    # Query the database to retreive commits
    commits = session.query(Commit).filter(
        and_(
            Commit.repository_full_name == repository_full_name,
            Commit.committer_date >= one_week_ago
        )
    ).all()
    
    # Array to store commit data
    commit_data = []

    for commit in commits:
        # Check for bots
        # if commit.committer_name is None or "bot" in commit.committer_name.lower() or "[bot]" in commit.committer_name.lower():
        #     continue
        
        data = {
            "message": commit.commit_message
        }

        commit_data.append(data)

    return commit_data

# COMMITS 2: Gets NUMBER of commits made within one_week_ago
def get_num_commits(commit_data):
    return len(commit_data)



# CONTRIBUTORS 1: Gets ALL contributors who are considered "active" within one_week_ago
# Active: > 0 commits this month, > 0 issues this month, > 0 PRs this month, or > 2 comments this month
# TODO: Filter out individuals such as TensorflowGardener (maybe), or look at PR and issue authors again.
def get_active_contributors(session, thirty_days_ago, repository_full_name):
    # Query the database to retreive commits
    commits = session.query(Commit).filter(
        and_(
            Commit.repository_full_name == repository_full_name,
            Commit.committer_date >= thirty_days_ago
        )
    ).all()
    
    # Query for pull requests
    pulls = session.query(PullRequest).filter(
        and_(
            PullRequest.repository_full_name == repository_full_name,
            PullRequest.created_at >= thirty_days_ago,
        )
    ).all()

    # Query for pull request comments
    pr_comments = session.query(PullRequestComment).filter(
        and_(
            PullRequestComment.repository_full_name == repository_full_name,
            PullRequestComment.created_at >= thirty_days_ago
        )
    )
    
    # Query the database for issues
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name,
            Issue.created_at >= thirty_days_ago,
        )
    ).all()

    # Query for issue comments
    issue_comments = session.query(IssueComment).filter(
        and_(
            IssueComment.repository_full_name == repository_full_name,
            IssueComment.created_at >= thirty_days_ago,
        )
    ).all()
    
    # Store active contributor data
    active_contributors = []
    
    # By number of commits
    for commit in commits:
        # if '[bot]' in commit.committer_name or 'bot' in commit.committer_name:
        #     continue

        author = commit.commit_author_name
        found = False
        
        for contributor in active_contributors:    
            if contributor['author'] == author:
                contributor['commits'] += 1
                found = True
                break
        if not found:
            contributor_data = {
                'author': author,
                'commits': 1,
                'pull_requests': 0,
                'issues': 0,
                'comments': 0
            }
            active_contributors.append(contributor_data)
        
    # By number of PRs
    for pr in pulls:
        if '[bot]' in pr.user_login.lower() or 'bot' in pr.user_login.lower():
            continue
        
        author = pr.user_login
        found = False 
        for contributor in active_contributors:
            if contributor['author'] == author:
                contributor['pull_requests'] += 1
                found = True
                break
        if not found:
            contributor_data = {
                'author': author,
                'commits': 0,
                'pull_requests': 1,
                'issues': 0,
                'comments': 0
            }
            active_contributors.append(contributor_data)
    
    # By number of issues
    for issue in issues:
        if '[bot]' in issue.user_login.lower() or 'bot' in issue.user_login.lower():
            continue
        
        author = issue.user_login
        found = False 
        for contributor in active_contributors:
            if contributor['author'] == author:
                contributor['issues'] += 1
                found = True
                break
        if not found:
            contributor_data = {
                'author': author,
                'commits': 0,
                'pull_requests': 0,
                'issues': 1,
                'comments': 0
            }
            active_contributors.append(contributor_data)
        
    # By number of issue comments
    for comment in issue_comments:
        if '[bot]' in comment.user_login.lower() or 'bot' in comment.user_login.lower():
            continue

        author = comment.user_login
        found = False

        for contributor in active_contributors:
            if contributor['author'] == author:
                contributor['comments'] += 1
                found = True
                break
        if not found:
            contributor_data = {
                'author': author,
                'commits': 0,
                'pull_requests': 0,
                'issues': 0,
                'comments': 1
            }
            active_contributors.append(contributor_data)

    # Loop through pull request comments
    for comment in pr_comments:
        if '[bot]' in comment.user_login.lower() or 'bot' in comment.user_login.lower():
            continue

        author = comment.user_login
        found = False

        for contributor in active_contributors:
            if contributor['author'] == author:
                contributor['comments'] += 1
                found = True
                break
        if not found:
            contributor_data = {
                'author': author,
                'commits': 0,
                'pull_requests': 0,
                'issues': 0,
                'comments': 1
            }
            active_contributors.append(contributor_data)
    
    commit_threshold = 0 # Commit threshold for being considered active
    pr_threshold = 0 # Pull requests in the last week
    issue_threshold = 0 # Issues created in the last month
    comment_threshold = 2 # Comments in the last month

    # Filter contributors who meet the activity threshold
    # Change conditional statement depending on what is considered "active"
    active_contributors = [
        contributor for contributor in active_contributors
        if contributor['comments'] > comment_threshold or contributor['commits'] > commit_threshold or contributor['pull_requests'] > pr_threshold or contributor['issues'] > issue_threshold
    ]
    num_contributors = len(active_contributors)
    active_contributors.append({"number_of_active_contributors": num_contributors})
    return active_contributors


# Retreive all data for a given repository and format
def get_repo_data(session, one_week_ago, thirty_days_ago, limit, repo_name):
        # ISSUES
        open_issues = get_open_issues(session, one_week_ago, repo_name)           
        closed_issues = get_closed_issues(session, one_week_ago, repo_name)                                                  
        
        # PRS
        open_pull_requests = get_open_prs(session, one_week_ago, repo_name)            
        closed_pull_requests = get_closed_prs(session, one_week_ago, repo_name)           
        
        # COMMITS
        commits = get_commit_messages(session, one_week_ago, repo_name)
        
        # Format and store data
        repo_data = {
            "repo_name": repo_name,
            "open_issues": open_issues,
            "closed_issues": closed_issues,
            "active_issues": get_active_issues(session, one_week_ago, repo_name),
            "stale_issues": get_stale_issues(session, one_week_ago, repo_name, thirty_days_ago),
            "num_weekly_open_issues": get_num_open_issues_weekly(open_issues),
            "num_weekly_closed_issues": get_num_closed_issues_weekly(closed_issues),
            "open_pull_requests": open_pull_requests,
            "closed_pull_requests": closed_pull_requests,
            "num_open_prs": get_num_open_prs(open_pull_requests),
            "num_closed_prs": get_num_closed_prs(closed_pull_requests),
            "commits": commits,
            "num_commits": get_num_commits(commits),
            "active_contributors": get_active_contributors(session, thirty_days_ago, repo_name),
            "latest_release": get_latest_release(session, repo_name) 
        }
        return repo_data

# Fetch GitHub ReadMe

def fetch_github_readme_direct(repo_name):
    """
    Fetch README by constructing the raw GitHub URL from just the repository name
    
    Parameters:
    repo_name (str): Name of the repository

    Returns:
    str: README content or error message
    """
    # Construct base repository URL
    repo_url = f"https://github.com/{repo_name}"
    
    # Possible README variations and paths
    readme_variations = [
        '/raw/main/README.md',
        '/raw/master/README.md',
        '/raw/main/Readme.md',
        '/raw/main/readme.md',
        '/raw/main/README',
        '/raw/master/README'
    ]
    
    try:
        # Try different README paths
        for variation in readme_variations:
            try:
                response = requests.get(repo_url + variation)
                
                # If successful, return the content
                if response.status_code == 200:
                    return response.text
            
            except requests.RequestException:
                continue
        
        # If no README found
        return "404"
    
    except Exception as e:
        return f"Error fetching README: {str(e)}"



# Main 
if __name__ == '__main__':
    # Measure the time it takes for every function to execute. 
    start_time = time.time()
    database_path = 'github.db'

    engine = create_engine(f'sqlite:///{database_path}')

    # DATABASE SESSION
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Omit the SQL logs from printing on each run
    logging.disable(logging.WARNING)
        
    # Making a set to keep track of processed repos to save time
    processed_repos = set()
    
    # Get a list of repos in the database
    repo_list = [r[0] for r in session.query(Repository.full_name).all()]
     
    # Time variables and limit
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30) 
    limit = 100

    # Array to store data for all of the repositories
    all_repo_data = []

    # for-loop for every repo name (ex. tensorflow/tensorflow)
    for repo in repo_list:
        if repo in processed_repos:
            continue
        
        repo_data = get_repo_data(session, one_week_ago, thirty_days_ago, limit, repo)
        
        all_repo_data.append(repo_data)
        processed_repos.add(repo)
    
    for item in all_repo_data:
        print("repo_data = " + json.dumps(item, indent=4))
    
    # Check how long the function takes to run and print result
    elapsed_time = time.time() - start_time
    if (elapsed_time >= 60):
        print("This entire program took {:.2f} minutes to run".format(elapsed_time/60))
    else:
        print("This entire program took {:.2f} seconds to run".format(elapsed_time))
