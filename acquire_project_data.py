from github import Github
from datetime import datetime, timedelta



def get_issue_text(repo, one_week_ago):
    issue_text = ""
    issues = repo.get_issues(state='all', since=one_week_ago)

    for issue in issues:
        issue_text += f"Title: {issue.title}"
        issue_text += f"Body: {issue.body}\n"

        comments = issue.get_comments()
        for comment in comments:
            issue_text += f"Comment by {comment.user.login}: {comment.body}\n"
        issue_text += "--------------------------------------------------"

    return issue_text

def get_pr_text(repo, one_week_ago):
    return ""

def get_commit_messages(repo, one_week_ago):
    return ""


if __name__ == '__main__':
    PROJECT_NAME = 'tensorflow/tensorflow' 

    g = Github()
    repo = g.get_repo(PROJECT_NAME)

    one_week_ago = datetime.now() - timedelta(days=7)

    print(get_issue_text(repo, one_week_ago))

    g.close()