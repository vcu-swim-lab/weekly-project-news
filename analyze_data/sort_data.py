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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'build_database')))
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


load_dotenv()

# Checks the rate limit
def rate_limit_check(g):
    rate_limit = g.get_rate_limit().core
    if rate_limit.remaining < 10:  
        print("Approaching rate limit, pausing...")
        now = datetime.now(tz=timezone.utc)
        sleep_duration = max(0, (rate_limit.reset - now).total_seconds() + 10)  # adding 10 seconds buffer
        time.sleep(sleep_duration)

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

# ISSUES 3: Get list of "active" issues, which are issues commented on/updated within the last week
def get_active_issues(session, one_week_ago, repository_full_name):
    # Retreive issues and set up variables
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name, 
            Issue.state == 'open', 
            Issue.updated_at >= one_week_ago
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
            "comments": []
        }
        
        # Query comments
        comments = session.query(IssueComment).filter(IssueComment.issue_id == issue.id).all()
        for comment in comments:
            issue_data["comments"].append({"body": comment.body})
        
        active_issue_data.append(issue_data)

    
    return active_issue_data

  
# ISSUES 4: Gets all issues, sorted by longest open date first
def sort_issues_open_date(session, repository_full_name, limit): 
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name, 
            Issue.state == 'open', 
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

# ISSUES 5: Gets all issues within one_week_ago, sorted by most comments first
def sort_issues_num_comments(session, repository_full_name, limit):
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name, 
            Issue.state == 'open', 
        )
    ).order_by(
        Issue.comments.desc()
    ).all()
    
    issue_data = []
    
    
    # Iterates through each issue
    for issue in issues:
        # Omit bots
        if "bot" in issue.user_login.lower() or "[bot]" in issue.user_login.lower():
            continue
        
        # If the number of comments on an issue is 0, skip it
        if issue.comments == 0:
            continue
        
        # Otherwise, add the title and number of comments to the data array
        data = {
        "title": issue.title,
        "number_of_comments": issue.comments,
        "body": issue.body,
        "url": issue.html_url,
        "id": issue.id,
        "comments": []
        }
        comments = session.query(IssueComment).filter(IssueComment.issue_id == issue.id).all()
        for comment in comments:
            data["comments"].append({"body": comment.body})
        
        issue_data.append(data)
        
        # Break the for loop if the amount of data is large enough
        if len(issue_data) >= limit:
            break
 
    return issue_data # Return in JSON format

# ISSUES 6: Get average time to close issues in the last week 
def avg_issue_close_time_weekly(session, one_week_ago, repository_full_name):
    # Retreive the issues and set up time variables
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name, 
            Issue.state == 'closed',
            Issue.closed_at >= one_week_ago
        )
    ).all()
    
    total_issues = len(issues)
    total_close_time = 0
    avg_close_time = 0
    
    # Iterates through each issue and calculates the total close time in minutes for each issue
    for issue in issues:
        # Omit bots
        if "bot" in issue.user_login.lower() or "[bot]" in issue.user_login.lower():
            continue
        
        time_open = issue.closed_at - issue.created_at
        total_minutes = time_open.total_seconds() // 60
        total_close_time += total_minutes # Adds total minutes to the total number of minutes to close issues
    
    # Prevents dividing by zero
    if total_issues > 0:
        avg_close_time = ((total_close_time / total_issues) / 60) / 24 # Calculates the average time to close in days
    
    
    # Return the average time to close issues in the last week formatted to 2 decimals
    return  "{:.2f} days".format(avg_close_time)

# ISSUES 7: Get number of open issues in the last week
def get_num_open_issues_weekly(weekly_open_issues):
    return len(weekly_open_issues)

# ISSUES 8: Get number of closed issues in the last week
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
                "url": pr.html_url
            }
        
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
                "url": pr.html_url
            }
        
        closed_pr_data.append(pr_data)

    return closed_pr_data

# PRS 3: Get "active" pull requests (updated within the last week)
def get_active_prs(session, one_week_ago, repository_full_name):
    # Query the database for pull requests
    pulls = session.query(PullRequest).filter(
        and_(
            PullRequest.repository_full_name == repository_full_name, 
            PullRequest.state == 'open', 
            PullRequest.updated_at >= one_week_ago 
        )
    ).all()
    
    active_pr_data = []
    
    
    # Loop through each PR
    for pr in pulls:
        # Omit bots
        if "bot" in pr.user_login.lower() or "[bot]" in pr.user_login.lower():
            continue
        
        pr_data = {
                "title": pr.title,
                "user": pr.user_login,
                "body": pr.body,
                "url": pr.html_url,
                "comments": []
            }
        
        # Query PR comments and loop through them
        comments = session.query(PullRequestComment).filter(PullRequestComment.pull_request_id == pr.id).all()
        for comment in comments:
            pr_data["comments"].append({"body": comment.body})

        active_pr_data.append(pr_data)

    return active_pr_data

# PRS 4: Get NUMBER of OPEN pull requests made within one_week_ago
def get_num_open_prs(pr_data_open):
    return len(pr_data_open)

# PRS 5: Get NUMBER of CLOSED pull requests made within one_week_ago
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
# Active: > 0 commits this month, > 0 issues this month, AND > 0 PRs this month
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
    
    # Query the database for issues
    issues = session.query(Issue).filter(
        and_(
            Issue.repository_full_name == repository_full_name,
            Issue.created_at >= thirty_days_ago,
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
                'issues': 0
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
                'issues': 0
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
                'issues': 1
            }
            active_contributors.append(contributor_data)
        
    
    commit_threshold = 0 # Commit threshold for being considered active
    pr_threshold = 0 # Pull requests in the last week
    issue_threshold = 0 # Issues created in the last month

    # Filter contributors who meet the activity threshold
    # Change conditional statement depending on what is considered "active"
    active_contributors = [
        contributor for contributor in active_contributors
        if contributor['commits'] > commit_threshold or contributor['pull_requests'] > pr_threshold or contributor['issues'] > issue_threshold
    ]
    
    num_active_contributors = len(active_contributors) # Gets number of active contributors
    active_contributors.append({'number_of_active_contributors': num_active_contributors}) # Add to data set

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
            "num_weekly_open_issues": get_num_open_issues_weekly(open_issues),
            "num_weekly_closed_issues": get_num_closed_issues_weekly(closed_issues),
            "issues_by_open_date": sort_issues_open_date(session, repo_name, limit),
            "issues_by_number_of_comments": sort_issues_num_comments(session, repo_name, limit),
            "average_issue_close_time_weekly": avg_issue_close_time_weekly(session, one_week_ago, repo_name),
            "open_pull_requests": open_pull_requests,
            "closed_pull_requests": closed_pull_requests,
            "active_pull_requests": get_active_prs(session, one_week_ago, repo_name),
            "num_open_prs": get_num_open_prs(open_pull_requests),
            "num_closed_prs": get_num_closed_prs(closed_pull_requests),
            "commits": commits,
            "num_commits": get_num_commits(commits),
            "active_contributors": get_active_contributors(session, thirty_days_ago, repo_name)
        }
        
        return repo_data

# Main 
if __name__ == '__main__':
    # Measure the time it takes for every function to execute. 
    start_time = time.time()
    database_path = '../build_database/github.db'
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
    
    