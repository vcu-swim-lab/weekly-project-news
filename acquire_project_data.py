from github import Github
from datetime import datetime, timedelta, timezone
import time
import json

def rate_limit_check(g):
    rate_limit = g.get_rate_limit().core
    if rate_limit.remaining < 10:  
        print("Approaching rate limit, pausing...")
        now = datetime.now(tz=timezone.utc)
        sleep_duration = max(0, (rate_limit.reset - now).total_seconds() + 10)  # adding 10 seconds buffer
        time.sleep(sleep_duration)

def get_issue_text(g, repo, one_week_ago):
    issue_text = "Issues:\n"
    issues = repo.get_issues(state='all', since=one_week_ago)

    for issue in issues:
        issue_text += f"Title: {issue.title}\n"
        issue_text += f"Body: {issue.body}\n"

        comments = issue.get_comments()
        for comment in comments:
            issue_text += f"\tComment by {comment.user.login}: {comment.body}\n"
        issue_text += "--------------------------------------------------\n"

        rate_limit_check(g)

    return issue_text

# Gets the text from pull requests, including title, body, and state.
def get_pr_text(g, repo, one_week_ago):
    pr_text = "PRs:\n"
    pulls = repo.get_pulls(state='all', sort='created')
    
    for pr in pulls:
        pr_text += f"Title: {pr.title}\n"
        pr_text += f"Body: {pr.body}\n"
        pr_text += f"State: {pr.state}\n"
        pr_text += "--------------------------------------------------\n"
        rate_limit_check(g)
    
    return pr_text

def get_commit_messages(g, repo, one_week_ago):
    commit_text = "Commits:\n"
    commits = repo.get_commits(since=one_week_ago)

    for commit in commits:
        commit_text += f"Author: {commit.commit.author.name}\n"
        commit_text += f"Message: {commit.commit.message}\n"
        commit_text += "--------------------------------------------------\n"
        rate_limit_check(g)

    return commit_text


if __name__ == '__main__':

    # get all of the subscribers from subscribers.json
    with open('subscribers.json') as file:
        subscribers_data = json.load(file)

    # get a list of all of the repo names from subscribers_data
    repo_names = [subscriber['metadata']['repo_name'] for subscriber in subscribers_data['results']]

    # pygithub
    g = Github()
    one_week_ago = datetime.now() - timedelta(days=7)

    # for-loop for every repo name (ex. tensorflow/tensorflow)
    for repo_url in repo_names:
        # project_name = anything after github.com/ (ex. tensorflow/tensorflow)
        PROJECT_NAME = repo_url.split('https://github.com/')[-1]

        # commenting this out to test my own personal repo lol
        # repo = g.get_repo(PROJECT_NAME)

        repo = g.get_repo('stevenbui44/test-vscode')


        print(get_issue_text(g, repo, one_week_ago))
        print(get_pr_text(g, repo, one_week_ago))
        print(get_commit_messages(g, repo, one_week_ago))

        # OUTPUT EVERYTHING AS A JSON FILE
        #Sample JSON code

        
        dict = {
        "issues": get_issue_text(g, repo, one_week_ago),
        "pull requests": get_pr_text(g, repo, one_week_ago),
        "commits": get_commit_messages(g, repo, one_week_ago)
        }
        with open("data.json", "w") as outfile:
            json.dump(dict, outfile, indent=2)
        

    g.close()