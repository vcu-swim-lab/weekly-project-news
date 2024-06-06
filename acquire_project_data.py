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
        if "[bot]" not in issue.user.login.lower() and "bot" not in issue.user.login.lower():
            issue_data = {
                "title": issue.title,
                "body": issue.body,
                "user": issue.user.login,
                "state": issue.state,
                # "created_at": issue.created_at.isoformat(),
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

# formats a specific repo's PRs as json data
def get_pr_text(g, repo, one_week_ago):
    pr_data_all = []
    pulls = repo.get_pulls(state='all', sort='created', direction='desc')

    for pr in pulls:
        if pr.created_at <= one_week_ago:
            break
        if "[bot]" not in pr.user.login.lower() and "bot" not in pr.user.login.lower():
            pr_data = {
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "user": pr.user.login
                # "created_at": pr.created_at.isoformat()
            }
            pr_data_all.append(pr_data)
        rate_limit_check(g)
    
    return pr_data_all

# formats a specific repo's commit messages as json data
def get_commit_messages(g, repo, one_week_ago):
    commit_data_all = []
    commits = repo.get_commits(since=one_week_ago)

    for commit in commits:
        if commit.author is not None and "[bot]" not in commit.author.login.lower() and "bot" not in commit.author.login.lower():
            commit_data = {
                "author": commit.commit.author.name,
                "message": commit.commit.message
                # "created_at": commit.commit.author.date.isoformat()
            }

            commit_data_all.append(commit_data)
        rate_limit_check(g)

    return commit_data_all

# Retrieves and sorts the issues that have been opened the longest
# Issues opened within the last week? Put one_week_ago in the parameters and since=one_week_ago in get_issues()
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

# NOTE: Christian is working on this right now
# Retrieves the number of new contributors in the last week.
def get_new_contributors(g, repo, one_week_ago):
    new_contributor_data = []
    commits = repo.get_commits(since=one_week_ago)
    num_new_contributors = 0

    for commit in commits:
        commit_author = commit.author
        author_commits = repo.get_commits(author=commit_author)
        first_commit = None

        for c in author_commits:
            first_commit = c
            break

        if first_commit and first_commit.commit.committer.date.replace(tzinfo=None) >= one_week_ago.replace(tzinfo=None):
            data = {
                "author": commit.commit.author.name,
                "description": "new contributor"
            }
            num_new_contributors+=1
            new_contributor_data.append(data)
    
    # Can turn to string if needed with str(num_new_contributors)
    new_contributor_data.append({"number_of_new_contributors": num_new_contributors})
    return new_contributor_data

# NOTE: Christian is working on this right now
# Get total number of contributors in the last week (even if they've contributed before)
def get_weekly_contributors(g, repo, one_week_ago):
    contributor_data = []
    commits = repo.get_commits(since=one_week_ago)
    num_weekly_contributors = 0

    for commit in commits:
        if commit.commit.author.name not in contributor_data:
            data = {
                "author": commit.commit.author.name,
                "description": "contributed this week"
            }
            contributor_data.append(data)
            num_weekly_contributors += 1
    contributor_data.append({"number_of_weekly_contributors": num_weekly_contributors})
    
    return contributor_data

# Gets the total number of commits in the last week
def get_num_commits(g, repo, one_week_ago):
    commits = repo.get_commits(since=one_week_ago).totalCount
    return commits

# Gets the total number of PRs in the last week
def get_num_prs(prs_data):
    return len(prs_data)

#TODO
# Get the issues with the most comments

#TODO
# Get the number and list the contributors who have made more than one(or more) commit in the last week? Month? 



if __name__ == '__main__':

    # get all of the subscribers from subscribers.json
    with open('test_monica_subscribers.json') as file:
        subscribers_data = json.load(file)

    # get a list of all of the repo names from subscribers_data
    repo_names = [subscriber['metadata']['repo_name'] for subscriber in subscribers_data['results']]

    # pygithub
    g = Github(os.environ['GITHUB_API_KEY'])
    one_week_ago = datetime.now(timezone.utc) - timedelta(weeks=3)
    data = []

    # for-loop for every repo name (ex. tensorflow/tensorflow)
    for repo_url in repo_names:
        # project_name = anything after github.com/ (ex. tensorflow/tensorflow)
        PROJECT_NAME = repo_url.split('https://github.com/')[-1]
        
        repo = g.get_repo(PROJECT_NAME)
    
        # saves one repo's data
        pr_data = get_pr_text(g, repo, one_week_ago)
        repo_data = {
            # "repo_name": PROJECT_NAME,
            # "issues": get_issue_text(g, repo, one_week_ago),
            "pull_requests": pr_data,
            "commits": get_commit_messages(g, repo, one_week_ago),
            # "issues_by_open_date": sort_issues(g, repo)
            # "new_contributors": get_new_contributors(g, repo, one_week_ago),
            # "weekly_contributors": get_weekly_contributors(g, repo, one_week_ago),
            "num_commits": get_num_commits(g, repo, one_week_ago),
            "num_prs": get_num_prs(pr_data)
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