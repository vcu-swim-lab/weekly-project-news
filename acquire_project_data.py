from github import Github
from datetime import datetime, timedelta, timezone
import time


def rate_limit_check(g):
    rate_limit = g.get_rate_limit().core
    if rate_limit.remaining < 10:  
        print("Approaching rate limit, pausing...")
        now = datetime.now(tz=timezone.utc)
        sleep_duration = max(0, (rate_limit.reset - now).total_seconds() + 10)  # adding 10 seconds buffer
        time.sleep(sleep_duration)

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

def get_pr_text(g, repo, one_week_ago):
    ### TODO
    return ""

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