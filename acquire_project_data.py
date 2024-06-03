from github import Github
from datetime import datetime, timedelta, timezone
import time

# Function that checks the rate limit of the GitHub API to make sure that we don't hit the rate limit
def rate_limit_check(g):
    rate_limit = g.get_rate_limit().core
    if rate_limit.remaining < 10:  
        print("Approaching rate limit, pausing...")
        now = datetime.now(tz=timezone.utc)
        sleep_duration = max(0, (rate_limit.reset - now).total_seconds() + 10)  # adding 10 seconds buffer
        time.sleep(sleep_duration)

# Function that gets issues from a given repo and formats it as text
def get_issue_text(g, repo, one_week_ago):
    issue_text = ""
    issues = repo.get_issues(state='all', since=one_week_ago)

    for issue in issues:
        issue_text += f"Title: {issue.title}"
        issue_text += f"Body: {issue.body}\n"

        comments = issue.get_comments()
        for comment in comments:
            issue_text += f"Comment by {comment.user.login}: {comment.body}\n"
        issue_text += "--------------------------------------------------"
        rate_limit_check(g)

    return issue_text

# Function that gets PRs from a given repo and formats it as text
def get_pr_text(g, repo, one_week_ago):
    pr_text = ""
    prs = repo.get_prs(state='all', since=one_week_ago)

    for pr in prs:
        pr_text += f"Title: {pr.title}"
        pr_text += f"Body: {pr.body}\n"

        comments = pr.get_issue_comments()
        for comment in comments:
            pr_text += f"Comment by {comment.user.login}: {comment.body}\n"
        pr_text += "--------------------------------------------------\n"
        rate_limit_check(g)

    return pr_text

def get_commit_messages(g, repo, one_week_ago):
    ### TODO
    return ""


if __name__ == '__main__':
    PROJECT_NAME = 'tensorflow/tensorflow' 

    g = Github()
    repo = g.get_repo(PROJECT_NAME)

    one_week_ago = datetime.now() - timedelta(days=7)

    print(get_issue_text(g, repo, one_week_ago))

    # OUTPUT EVERYTHING AS A JSON FILE

    g.close()