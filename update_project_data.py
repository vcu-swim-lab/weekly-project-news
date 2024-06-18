import sqlite3
from github import Github
from datetime import datetime, timedelta, timezone
import time
import json
import os
import requests
from dotenv import load_dotenv
import concurrent.futures
import multiprocessing
from acquire_project_data import *
from enum import Enum

load_dotenv()

#TODO Implement multiprocessing and scheduling for every week (or do scheduling in another file like run_newsletter.py)

# Script to update repositories.db
# Connect to the database
conn = sqlite3.connect('repositories.db')
cursor = conn.cursor()
    

# Time variable for function parameters. Holds the date/time one week ago
one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

# ISSUES 1: Update the open issues column
def update_open_issues(repo_name, open_issues):
    try:
        open_issues_json = json.dumps(open_issues)
        cursor.execute("UPDATE repositories SET open_issues = ? WHERE repo_name = ?", (open_issues_json, repo_name,))
        conn.commit()
        print(f"Updated open issues for repository {repo_name}")
    except Exception as e:
        print(e)
        conn.rollback()

# ISSUES 2: Update the closed issues column
def update_closed_issues(repo_name, closed_issues):
    try:
        closed_issues_json = json.dumps(closed_issues)
        cursor.execute("UPDATE repositories SET closed_issues = ? WHERE repo_name = ?", (closed_issues_json, repo_name,))
        conn.commit()
        print(f"Updated closed issues for repository {repo_name}")
    except Exception as e:
        print(e)
        conn.rollback()

        
# ISSUES 3: Update sort_open_date column
def update_sort_open_date(self, repo_name):
    print()

# ISSUES 4: Update sort_comments column
def update_sort_comments(self, repo_name):
    print()
    
# ISSUES 5: Update the number of weekly open issues
def update_num_weekly_open_issues(repo_name, num_weekly_open_issues):
    try:
        num_weekly_open_issues_json = json.dumps(num_weekly_open_issues)
        cursor.execute("UPDATE repositories SET num_weekly_open_issues = ? WHERE repo_name = ?", (num_weekly_open_issues_json, repo_name,))
        conn.commit()
        print(f"Updated number of weekly open issues for repository {repo_name}")
    except Exception as e:
        print(e)
        conn.rollback()
        

# ISSUES 6: Update the number of weekly closed issues
def update_num_weekly_closed_issues(repo_name, num_weekly_closed_issues):
    try:
        num_weekly_closed_issues_json = json.dumps(num_weekly_closed_issues)
        cursor.execute("UPDATE repositories SET num_weekly_closed_issues = ? WHERE repo_name = ?", (num_weekly_closed_issues_json, repo_name,))
        conn.commit()
        print(f"Updated number of weekly closed issues for repository {repo_name}")
    except Exception as e:
        print(e)
        conn.rollback()

# ISSUES 7: Update the average close time for all time
def update_avg_issue_close_time(repo_name, avg_issue_close_time):
    print()

# ISSUES 8: Update the weekly average close time
def update_avg_issue_close_time_weekly(repo_name, avg_issue_close_time_weekly):
    print()

# ISSUES 9: Update the list of active issues
def update_active_issues(repo_name, active_issues):
    print()
    


# PRS 1: Update open pull requests
def update_open_pull_requests(repo_name, open_prs):
    try:
        open_prs_json = json.dumps(open_prs)
        cursor.execute("UPDATE repositories SET open_pull_requests = ? WHERE repo_name = ?", (open_prs_json, repo_name))
        conn.commit()
        print(f"Updated open pull requests for repository {repo_name}")
    except Exception as e: 
        print(e)
        conn.rollback()
        
# PRS 2: Update closed pull requests
def update_closed_pull_requests(repo_name, closed_prs):
    try:
        closed_prs_json = json.dumps(closed_prs)
        cursor.execute("UPDATE repositories SET closed_pull_requests = ? WHERE repo_name = ?", (closed_prs_json, repo_name))
        conn.commit()
        print(f"Updated closed pull requests for repository {repo_name}")
    except Exception as e: 
        print(e)
        conn.rollback()
        

# PRS 3: Update number of open pull requests
def update_num_open_prs(repo_name, num_open_prs):
    try:
        num_open_prs_json = json.dumps(num_open_prs)
        cursor.execute("UPDATE repositories SET num_open_prs = ? WHERE repo_name = ?", (num_open_prs_json, repo_name))
        conn.commit()
        print(f"Updated number of open pull requests requests for repository {repo_name}")
    except Exception as e: 
        print(e)
        conn.rollback()

# PRS 4: Update number of closed pull requests
def update_num_closed_prs(repo_name, num_closed_prs):
    try:
        num_closed_prs_json = json.dumps(num_closed_prs)
        cursor.execute("UPDATE repositories SET num_closed_prs = ? WHERE repo_name = ?", (num_closed_prs_json, repo_name))
        conn.commit()
        print(f"Updated number of closed pull requests requests for repository {repo_name}")
    except Exception as e: 
        print(e)
        conn.rollback()
        
        
        
# COMMITS 1: Update list of commits
def update_commits(repo_name, commits):
    try:
        commits_json = json.dumps(commits)
        cursor.execute("UPDATE repositories SET commits = ? WHERE repo_name = ?", (commits_json, repo_name))
        conn.commit()
        print(f"Updated commits for repository {repo_name}")
    except Exception as e: 
        print(e)
        conn.rollback()
        
# COMMITS 2: Update the number of commits this week
def update_num_commits(repo_name, num_commits):
    try:
        num_commits_json = json.dumps(num_commits)
        cursor.execute("UPDATE repositories SET num_commits = ? WHERE repo_name = ?", (num_commits_json, repo_name))
        conn.commit()
        print(f"Updated the number of commits for repository {repo_name}")
    except Exception as e: 
        print(e)
        conn.rollback()


# CONTRIBUTORS 1: Update the list of new contributors
def update_new_contributors(repo_name, new_contributors):
    try:
        new_contributors_json = json.dumps(new_contributors)
        cursor.execute("UPDATE repositories SET new_contributors = ? WHERE repo_name = ?", (new_contributors_json, repo_name))
        conn.commit()
        print(f"Updated the new contributors for repository {repo_name}")
    except Exception as e: 
        print(e)
        conn.rollback()

# CONTRIBUTORS 2: Update the list of individuals who contributed this week

# CONTRIBUTORS 3: Update the list of active contributors


# Retreive the repository names
def get_repo_names(directory):
    repo_names = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as file:
                data = json.load(file)
                repo_name = data.get('repo_name')
                if repo_name:
                    repo_names.append(repo_name)
    return repo_names


# MAIN        
if __name__ == "__main__":
    # Measure the time it takes for every function to execute. 
    start_time = time.time()

    g = Github(os.environ['GITHUB_API_KEY'])
     
    # Time variables
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30) 
    
    # Limit the number of requests in certain pages (limits number of items in for loop)
    limit = 100
    
    # Define the directory and retreive the repo names
    directory = 'github_data'
    if not os.path.exists(directory):
        print("No such directory")
        
    repo_names = get_repo_names(directory)
        
        
    for repo_name in repo_names:
        print(repo_name)
        # Get the repository
        repo = g.get_repo(repo_name)
        
        # Fetch data using multiprocessing
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # ISSUES
            open_issues = executor.submit(get_open_issues, g, repo, one_week_ago)
            closed_issues = executor.submit(get_closed_issues, g, repo, one_week_ago)
            num_weekly_open_issues = executor.submit(get_num_open_issues_weekly, open_issues.result())
            num_weekly_closed_issues = executor.submit(get_num_closed_issues_weekly, closed_issues.result())
            
            # PRS
            open_pull_requests = executor.submit(get_open_prs, g, repo, one_week_ago)
            closed_pull_requests = executor.submit(get_closed_prs, g, repo, one_week_ago)
            num_open_prs = executor.submit(get_num_open_prs, open_pull_requests.result())  
            num_closed_prs = executor.submit(get_num_closed_prs, closed_pull_requests.result())
            
            # COMMITS
            commits = executor.submit(get_commit_messages, g, repo, one_week_ago)
            num_commits = executor.submit(get_num_commits, commits.result())
            
            # CONTRIBUTORS
            new_contributors = executor.submit(get_new_contributors, g, repo, one_week_ago)

        # ISSUE UPDATES
        update_open_issues(repo_name, open_issues.result())
        update_closed_issues(repo_name, closed_issues.result())
        update_num_weekly_open_issues(repo_name, num_weekly_open_issues.result())
        update_num_weekly_closed_issues(repo_name, num_weekly_closed_issues.result())
        
        # PR UPDATES
        update_open_pull_requests(repo_name, open_pull_requests.result())
        update_closed_pull_requests(repo_name, closed_pull_requests.result())
        update_num_open_prs(repo_name, num_open_prs.result())
        update_num_closed_prs(repo_name, num_closed_prs.result())
        
        # COMMIT UPDATES
        update_commits(repo_name, commits.result())
        update_num_commits(repo_name, num_commits.result())
        
        # CONTRIBUTOR UPDATES
        update_new_contributors(repo_name, new_contributors.result())
    
    
    # Check how long the function takes to run and print result
    elapsed_time = time.time() - start_time
    if (elapsed_time >= 60):
        print("This entire program took {:.2f} minutes to run".format(elapsed_time/60))
    else:
        print("This entire program took {:.2f} seconds to run".format(elapsed_time))

    # Close the connection
    conn.close()