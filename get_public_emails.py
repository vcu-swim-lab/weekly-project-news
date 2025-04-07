import requests
from datetime import datetime, timedelta, timezone
import time
import os
import json
import csv

# This script retrieves the emails from public repository commits

def get_recent_commit_emails(api_key, repo, days=365):
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
    
    email_commit_count = {}
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
            if commit['commit']['author'] and commit['commit']['author'].get('email'):
                email = commit['commit']['author']['email']
                email_commit_count[email] = email_commit_count.get(email, 0) + 1
            if commit['commit']['committer'] and commit['commit']['committer'].get('email'):
                email = commit['commit']['committer']['email']
                email_commit_count[email] = email_commit_count.get(email, 0) + 1
        
        page += 1
        
        if int(response.headers.get('X-RateLimit-Remaining', 0)) == 0:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            sleep_time = max(reset_time - int(time.time()), 0)
            print(f"Rate limit reached. Sleeping for {sleep_time} seconds.")
            time.sleep(sleep_time + 1)
    
    return email_commit_count



def get_repo_contributors(api_key, repo):
    output_file="contributors.json"
    base_url = "https://api.github.com"
    headers = {
        "Authorization": f"token {api_key}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    contributors_url = f"{base_url}/repos/{repo}/contributors"
    params = {
        "per_page": 100
    }
    
    contributors = []
    page = 1
    
    while True:
        params["page"] = page
        response = requests.get(contributors_url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching contributors for {repo}: {response.status_code}")
            break
        
        page_contributors = response.json()
        if not page_contributors:
            break
        
        for contributor in page_contributors:
            contributors.append({
                "login": contributor.get("login"),
                "contributions": contributor.get("contributions"),
                "url": contributor.get("html_url")
            })
        
        page += 1
        
        if int(response.headers.get('X-RateLimit-Remaining', 0)) == 0:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            sleep_time = max(reset_time - int(time.time()), 0)
            print(f"Rate limit reached. Sleeping for {sleep_time} seconds.")
            time.sleep(sleep_time + 1)
    
    os.makedirs("contributor_data", exist_ok=True)
    owner, repo_name = repo.split('/')
    
    # Save to JSON file
    output_file = f"contributor_data/{repo_name}_contributors.json"
    with open(output_file, "w") as json_file:
        json.dump(contributors, json_file, indent=4)
    print(f"Contributors for {repo} saved to {output_file}")

def get_recent_issues_and_prs(api_key, repo):
    base_url = "https://api.github.com"
    headers = {
        "Authorization": f"token {api_key}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    since_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    endpoints = [
        f"/repos/{repo}/issues",
    ]

    user_associations = {}
    
    for endpoint in endpoints:
        page = 1
        while True:
            params = {"since": since_date, "per_page": 100, "page": page}
            response = requests.get(f"{base_url}{endpoint}", headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching data from {endpoint} for {repo}: {response.status_code}")
                break
            
            items = response.json()
            if not items:
                break
            
            for item in items:
                if "pull_request" in item:
                    continue
                
                user = item["user"]["login"]
                association = item["author_association"]
                
                if user not in user_associations:
                    user_associations[user] = association
            
            page += 1
            
            if int(response.headers.get("X-RateLimit-Remaining", 0)) == 0:
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                sleep_time = max(reset_time - int(time.time()), 0)
                print(f"Rate limit reached. Sleeping for {sleep_time} seconds.")
                time.sleep(sleep_time + 1)
    
    return user_associations


def process_repositories(api_key, repositories):
    results = {}
    for repo in repositories:
        email_commit_count = get_recent_commit_emails(api_key, repo)
        email_commit_count = {email: count for email, count in email_commit_count.items() if "noreply" not in email}
        # Cut the list to half size, keeping the users with the least number of commits
        cutoff = len(email_commit_count) // 2
        sorted_committers = sorted(email_commit_count.items(), key=lambda x: x[1])
        email_commit_count = dict(sorted_committers[:cutoff])
        results[repo] = email_commit_count
    return results

def format_output(results):
    output = ""
    for repo, email_commit_count in results.items():
        output += f"{repo}: {len(email_commit_count)} contributors\n"
        sorted_contributors = sorted(email_commit_count.items(), key=lambda x: x[1], reverse=True)
        for email, count in sorted_contributors:
            output += f"{email}, {count} commits\n"
        output += "\n"
    return output.strip()


def save_to_csv(results, filename="github_email_commits.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Email", "Commits"])
        for repo, email_commit_count in results.items():
            writer.writerow([f"{repo}: {len(email_commit_count)} contributors"])
            for email, count in email_commit_count.items():
                writer.writerow([email, count])
    print(f"Data saved to {filename}")


# Main
if __name__ == '__main__':
    GITHUB_API_KEY = os.environ['GITHUB_API_KEYS'].split(' ')[0]
    repositories = [
        'tensorflow/tensorflow',
        'matplotlib/matplotlib',
        'django/django',
        'pytorch/pytorch',
        'facebook/react',
        'nodejs/node',
        'jenkinsci/jenkins',
        'ggerganov/llama.cpp',
        'storybookjs/storybook',
        'Avaiga/taipy',
        'CopilotKit/CopilotKit',
        'shadcn-ui/ui',
        'mermaid-js/mermaid',
        'freeCodeCamp/freeCodeCamp',
        'kanaries/pygwalker',
        'vuejs/core',
        'kubernetes/kubernetes',
        'twbs/bootstrap',
        'Microsoft/vscode',
        'docker/compose',
        'ansible/ansible',
        'nginx/nginx',
        'expressjs/express'
    ]
    
    results = process_repositories(GITHUB_API_KEY, repositories)
    formatted_output = format_output(results)
    
    print(formatted_output)
    
    with open('github_emails.txt', 'w') as f:
        f.write(formatted_output)
    save_to_csv(results)
    
    