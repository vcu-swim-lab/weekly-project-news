from github import Github
from datetime import datetime, timedelta, timezone, date
import time
import json
import os
from dotenv import load_dotenv

# If want to change time zone import this python package
# import pytz
# Example of using est
# est = pytz.timezone('America/New_York')

load_dotenv('public.env')  

# Checks the rate limit
def rate_limit_check(g):
    rate_limit = g.get_rate_limit().core
    if rate_limit.remaining < 10:  
        print("Approaching rate limit, pausing...")
        now = datetime.now(tz=timezone.utc)
        sleep_duration = max(0, (rate_limit.reset - now).total_seconds() + 10)  # adding 10 seconds buffer
        time.sleep(sleep_duration)

# ISSUES 1: Gets ALL issues within one_week_ago
def get_issue_text(g, repo, one_week_ago):
    issue_data_all = []
    issues = repo.get_issues(state='all', since=one_week_ago)

    for issue in issues:
        if "[bot]" not in issue.user.login.lower() and "bot" not in issue.user.login.lower():
            issue_data = {
                "title": issue.title,
                "body": issue.body,
                "user": issue.user.login,
                "state": issue.state,
                "comments": []
            }

            comments = issue.get_comments()
            for comment in comments:
                if "[bot]" not in comment.user.login.lower() and "bot" not in comment.user.login.lower():
                    comment_data = {
                        "user": comment.user.login,
                        "body": comment.body
                    }
                    issue_data["comments"].append(comment_data)

            issue_data_all.append(issue_data)
        rate_limit_check(g)

    return issue_data_all
  
# ISSUES 2: Gets all issues within one_week_ago, sorted by longest open date first
def sort_issues_open_date(g, repo): 
    issue_sort_data = []
    issues = repo.get_issues(state='open')
    for issue in issues:
        time_open = datetime.now(timezone.utc)-issue.created_at
        days = time_open.days
        hours, remainder = divmod(time_open.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        total_minutes = time_open.total_seconds() // 60

        issue_data = {
            "title": issue.title,
            "time_open": f"{days} days, {hours:02} hours, {minutes:02} minutes",
            "minutes_open": total_minutes,
            "url": issue.html_url
        }
        issue_sort_data.append(issue_data)
        rate_limit_check(g)
    
    issue_sort_data.sort(key=lambda x: x["minutes_open"], reverse=True)
    return issue_sort_data

# ISSUES 3: Gets all issues within one_week_ago, sorted by most comments first
def sort_issue_num_comments(g, repo):
    # Data array for the issues, retreives the issues from the repo
    issue_data = []
    issues = repo.get_issues(state='open')

    # Iterates through each issue
    for issue in issues:
        comments = issue.get_comments()
        num_comments = comments.totalCount # Retreives the number of comments on an issue
            
        # If the number of comments on an issue is 0, skip it
        if num_comments == 0:
            continue
        else: #Otherwise, add the title and number of comments to the data array
            # Can add more descriptors to data if needed
            data = {
            "title": issue.title,
            "number_of_comments": num_comments
            }
            issue_data.append(data)
    issue_data.sort(key=lambda x: x["number_of_comments"], reverse=True) # Sort the issues by number of comments
    return issue_data # Return in JSON format



# PRS 1: Gets open pull requests within one_week_ago
def get_open_prs(g, repo, one_week_ago):
    pr_data_open = []
    pulls = repo.get_pulls(state='open', sort='created', direction='desc')
    
    for pr in pulls:
        if pr.created_at <= one_week_ago:
            break
        if "[bot]" not in pr.user.login.lower() and "bot" not in pr.user.login.lower():
            pr_data = {
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "user": pr.user.login
            }
            pr_data_open.append(pr_data)
        rate_limit_check(g)
    
    return pr_data_open

# PRS 2: Gets closed pull requests within one_week_ago
def get_closed_prs(g, repo, one_week_ago):
    pr_data_closed = []
    pulls = repo.get_pulls(state='closed', sort='created', direction='desc')
    
    for pr in pulls:
        if pr.created_at <= one_week_ago:
            break
        if "[bot]" not in pr.user.login.lower() and "bot" not in pr.user.login.lower():
            pr_data = {
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "user": pr.user.login
            }
            pr_data_closed.append(pr_data)
        rate_limit_check(g)
    
    return pr_data_closed

# PRS 3: Gets NUMBER of ALL pull requests made within one_week_ago
def get_num_prs(pr_data_open, pr_data_closed):
    return len(pr_data_open) + len(pr_data_closed)

# PRS 4: Get NUMBER of OPEN pull requests made within one_week_ago
def get_num_open_prs(pr_data_open):
    return len(pr_data_open)

# PRS 5: Get NUMBER of CLOSED pull requests made within one_week_ago
def get_num_closed_prs(pr_data_closed):
    return len(pr_data_closed)



# COMMITS 1: Gets ALL commits within one_week_ago
def get_commit_messages(g, repo, one_week_ago):
    commit_data_all = []
    commits = repo.get_commits(since=one_week_ago)

    for commit in commits:
        if commit.author is not None and "[bot]" not in commit.author.login.lower() and "bot" not in commit.author.login.lower():
            commit_data = {
                "author": commit.commit.author.name,
                "message": commit.commit.message
            }

            commit_data_all.append(commit_data)
        rate_limit_check(g)

    return commit_data_all

# COMMITS 2: Gets NUMBER of commits made within one_week_ago
def get_num_commits(commit_data):
    return len(commit_data)



# CONTRIBUTORS 1: Gets NUMBER of new contributors who made their first commit within one_week_ago
def get_new_contributors(g, repo, one_week_ago):
    new_contributor_data = []
    commits = repo.get_commits(since=one_week_ago)
    num_new_contributors = 0
    processed_authors = set()

    # Loop through repo commits
    for commit in commits:
        # Filter through bot commits
        if '[bot]' in commit.commit.author.name:
            continue
        
        # Try retreiving author commits. If it doesn't work, print out error message.
        try:
            author_commits = repo.get_commits(author=commit.commit.author.name)
        except AssertionError as e:
            print(f"Skipping problematic commit: {e}")
            continue

        # Find author's first commit to analyze the date
        first_commit = None
        for c in author_commits:
            first_commit = c
            break
            
        # If commit is valid and within the last week, add it to the data array.
        if first_commit and (first_commit.commit.committer.date.replace(tzinfo=None) >= one_week_ago.replace(tzinfo=None)) and (first_commit.commit.author.name not in processed_authors):
            data = {
                "author": commit.commit.author.name,
                "description": "new contributor"
            }
            num_new_contributors+=1
            new_contributor_data.append(data)
            processed_authors.add(commit.commit.author.name)
        rate_limit_check(g)
    
    # Can turn to string if needed with str(num_new_contributors)
    new_contributor_data.append({"number_of_new_contributors": num_new_contributors})
    return new_contributor_data

# CONTRIBUTORS 2: Gets NUMBER of contributors who made any commits within one_week_ago
def get_weekly_contributors(g, repo, one_week_ago):
    contributor_data = []
    commits = repo.get_commits(since=one_week_ago)
    num_weekly_contributors = 0

    for commit in commits:
        if '[bot]' in commit.commit.author.name:
            continue
        if commit.commit.author.name not in contributor_data:
            data = {
                "author": commit.commit.author.name,
                "description": "contributed this week"
            }
            contributor_data.append(data)
            num_weekly_contributors += 1
    contributor_data.append({"number_of_weekly_contributors": num_weekly_contributors})
    
    return contributor_data

# CONTRIBUTORS 3: Gets ALL contributors who are considered "active" within one_week_ago
# Active: > 0 commits this week, > 0 issues this month, AND > 0 PRs this week
def get_active_contributors(g, repo, one_week_ago, thirty_days_ago):
    # Store active contributor data
    active_contributors = []
    
    # By number of commits
    commits = repo.get_commits(since=one_week_ago)
    for commit in commits:
        if '[bot]' in commit.commit.author.name:
            continue
        
        author = commit.commit.author.name
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
        
        rate_limit_check(g)
    
    # By number of PRs
    pulls = repo.get_pulls(state='all', sort='created')
    for pr in pulls:
        if '[bot]' in pr.user.login.lower():
            continue
        if pr.created_at <= one_week_ago:
            continue
        
        author = commit.commit.author.name
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
        
        rate_limit_check(g)

    # By number of issues
    issues = repo.get_issues(since=thirty_days_ago)
    for issue in issues:
        if '[bot]' in pr.user.login.lower():
            continue
        
        author = commit.commit.author.name
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
        
        rate_limit_check(g)
        
    
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
    active_contributors.append({'number_of_active_contributors': num_active_contributors})
    return active_contributors
    


# Main 
if __name__ == '__main__':
    # get all of the subscribers from subscribers.json
    with open('subscribers.json') as file:
        subscribers_data = json.load(file)

    # get a list of all of the repo names from subscribers_data
    repo_names = [subscriber['metadata']['repo_name'] for subscriber in subscribers_data['results']]

    # pygithub
    g = Github(os.environ['GITHUB_API_KEY'])
    
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Variable for saving the time 30 days ago, since timedelta doesn't define "one month" anywhere
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30) 

    data = []

    # for-loop for every repo name (ex. tensorflow/tensorflow)
    for repo_url in repo_names:
        # Testing my own repo 
        PROJECT_NAME = 'cnovalski1/APIexample'
        repo = g.get_repo(PROJECT_NAME)
    
        # saves one repo's data
        pr_data_open = get_open_prs(g, repo, one_week_ago)
        pr_data_closed = get_closed_prs(g, repo, one_week_ago)
        commit_data = get_commit_messages(g, repo, one_week_ago)
        repo_data = {
            "repo_name": PROJECT_NAME,
            "issues": get_issue_text(g, repo, one_week_ago),
            "issues_by_open_date": sort_issues_open_date(g, repo),
            "issues_by_number_of_comments": sort_issue_num_comments(g, repo),
            "open_pull_requests": pr_data_open,
            "closed_pull_requests": pr_data_closed,
            "num_all_prs": get_num_prs(pr_data_open, pr_data_closed),
            "num_open_prs": get_num_open_prs(pr_data_open),
            "num_closed_prs": get_num_closed_prs(pr_data_closed),
            "commits": commit_data,
            "num_commits": get_num_commits(commit_data),
            "new_contributors": get_new_contributors(g, repo, one_week_ago),
            "contributed_this_week": get_weekly_contributors(g, repo, one_week_ago),
            "active_contributors": get_active_contributors(g, repo, one_week_ago, thirty_days_ago)
        }

        data.append(repo_data)

        try:
            with open("testing-github_data.json", "w") as outfile:
                json.dump(data, outfile, indent=2)
            print(f"Successfully added {PROJECT_NAME} to github_data.json")
        except Exception as e:
            print(f"Error writing data for {PROJECT_NAME} to github_data.json")
            print(f"Error code: {e}")
    
    g.close()