from github import Github
from datetime import datetime, timedelta, timezone
import time
import json
import os
from dotenv import load_dotenv

# If want to change time zone import this python package
# import pytz
# Example of using est
# est = pytz.timezone('America/New_York')

load_dotenv('public.env')  

# checks the rate limit
def rate_limit_check(g):
    rate_limit = g.get_rate_limit().core
    if rate_limit.remaining < 10:  
        print("Approaching rate limit, pausing...")
        now = datetime.now(tz=timezone.utc)
        sleep_duration = max(0, (rate_limit.reset - now).total_seconds() + 10)  # adding 10 seconds buffer
        time.sleep(sleep_duration)

# formats a specific repo's issues as json data
def get_issue_text(g, repo, one_week_ago):
    issue_data_all = []
    issues = repo.get_issues(state='all', since=one_week_ago)

    for issue in issues:
        issue_data = {
            "title": issue.title,
            "body": issue.body,
            "user": issue.user.login,
            "state": issue.state,
            "comments": []
        }

        comments = issue.get_comments()
        for comment in comments:
            comment_data = {
                "user": comment.user.login,
                "body": comment.body
            }
            issue_data["comments"].append(comment_data)

        issue_data_all.append(issue_data)
        rate_limit_check(g)

    return issue_data_all

# formats a specific repo's PRs as json data
def get_pr_text(g, repo, one_week_ago):
    pr_data_all = []
    pulls = repo.get_pulls(state='all', sort='created')
    
    for pr in pulls:
        pr_data = {
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "user": pr.user.login
        }
        pr_data_all.append(pr_data)
        rate_limit_check(g)
    
    return pr_data_all

# formats a specific repo's commit messages as json data
def get_commit_messages(g, repo, one_week_ago):
    commit_data_all = []
    commits = repo.get_commits(since=one_week_ago)

    for commit in commits:
        commit_data = {
            "author": commit.commit.author.name,
            "message": commit.commit.message
        }

        commit_data_all.append(commit_data)
        rate_limit_check(g)

    return commit_data_all

# Retrieves and sorts the issues that have been opened the longest
def sort_issues(g, repo, one_week_ago):
    issue_sort_data = []
    issues = repo.get_issues(state='open', since=one_week_ago)
    for issue in issues:
        time_open = datetime.now(timezone.utc)-issue.created_at
        days = time_open.days
        hours, remainder = divmod(time_open.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        issue_data = {
            "title": issue.title,
            "time_open": f"{days} days, {hours:02} hours, {minutes:02} minutes",
            "url": issue.html_url,
        }
        issue_sort_data.append(issue_data)
        rate_limit_check(g)
    
    issue_sort_data.sort(key=lambda x: x["time_open"], reverse=True)
    return issue_sort_data


if __name__ == '__main__':

    # get all of the subscribers from subscribers.json
    with open('subscribers.json') as file:
        subscribers_data = json.load(file)

    # get a list of all of the repo names from subscribers_data
    repo_names = [subscriber['metadata']['repo_name'] for subscriber in subscribers_data['results']]

    # pygithub
    g = Github(os.environ['GITHUB_API_KEY'])
    one_week_ago = datetime.now() - timedelta(days=7)
    data = []

    # for-loop for every repo name (ex. tensorflow/tensorflow)
    for repo_url in repo_names:
        # Testing my own repo 
        PROJECT_NAME = 'cnovalski1/APIexample'
        repo = g.get_repo(PROJECT_NAME)

    
        # saves one repo's data
        
        repo_data = {
            "repo_name": PROJECT_NAME,
            "issues": get_issue_text(g, repo, one_week_ago),
            "pull_requests": get_pr_text(g, repo, one_week_ago),
            "commits": get_commit_messages(g, repo, one_week_ago),
            "sorted_issues": sort_issues(g, repo, one_week_ago)
        }

        data.append(repo_data)

        try:
            with open("github_data.json", "w") as outfile:
                json.dump(data, outfile, indent=2)
            print(f"Successfully added {PROJECT_NAME} to github_data.json")
        except Exception as e:
            print(f"Error writing data for {PROJECT_NAME} to github_data.json")
            print(f"Error code: {e}")

        

    g.close()