import requests
from datetime import datetime, timedelta, timezone
import time
import os

def get_recent_commit_emails(api_key, repo, days=7):
    base_url = "https://api.github.com"
    headers = {
        "Authorization": f"token {api_key}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    since_date = datetime.now(timezone.utc) - timedelta(days=days)
    since_date_str = since_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    commits_url = f"{base_url}/repos/{repo}/commits"
    params = {
        "since": since_date_str,
        "per_page": 100
    }
    
    emails = set()
    page = 1
    
    while True:
        params["page"] = page
        response = requests.get(commits_url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching commits for {repo}: {response.status_code}")
            break
        
        commits = response.json()
        if not commits:
            break
        
        for commit in commits:
            if commit['commit']['author'].get('email'):
                emails.add(commit['commit']['author']['email'])
            if commit['commit']['committer'].get('email'):
                emails.add(commit['commit']['committer']['email'])
        
        page += 1
        
        if int(response.headers.get('X-RateLimit-Remaining', 0)) == 0:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            sleep_time = max(reset_time - int(time.time()), 0)
            print(f"Rate limit reached. Sleeping for {sleep_time} seconds.")
            time.sleep(sleep_time + 1)
    
    return list(emails)

def process_repositories(api_key, repositories):
    results = {}
    for repo in repositories:
        emails = get_recent_commit_emails(api_key, repo)
        results[repo] = emails
    return results

def format_output(results):
    output = ""
    for repo, emails in results.items():
        output += f"{repo}: {len(emails)} emails\n"
        for email in emails:
            output += f"{email}\n"
        output += "\n"
    return output.strip()

# Main
if __name__ == '__main__':
    GITHUB_API_KEY = os.environ['GITHUB_API_KEY']
    repositories = [
        'tensorflow/tensorflow',
        'matplotlib/matplotlib',
        'django/django',
        'pytorch/pytorch',
        'facebook/react',
        'nodejs/node',
        'jenkinsci/jenkins'
    ]
    
    results = process_repositories(GITHUB_API_KEY, repositories)
    formatted_output = format_output(results)
    
    print(formatted_output)
    
    with open('github_emails.txt', 'w') as f:
        f.write(formatted_output)