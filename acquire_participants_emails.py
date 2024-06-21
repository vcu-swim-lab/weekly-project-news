import requests
import os
from dotenv import load_dotenv

load_dotenv()  

API_KEY = os.environ.get("GITHUB_API_KEY")

# GitHub API endpoint for searching repositories
github_api_url = "https://api.github.com/search/repositories"

# Parameters for the search query
params = {
    'q': 'pushed:>=2024-04-14',  # Commits pushed after this date (past week)
    'sort': 'updated',
    'order': 'desc',
    'per_page': 100  # Number of repositories to fetch
}

# GitHub API authentication (optional but recommended for higher rate limits)
# Replace with your GitHub username and personal access token
username = 'audreyylewis'
token = API_KEY
headers = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': f'token {token}'
}

# Send GET request to GitHub API
response = requests.get(github_api_url, params=params, headers=headers)

# Check if request was successful (status code 200)
if response.status_code == 200:
    # Parse JSON response
    data = response.json()
    repositories = data['items']

    # Filter repositories based on the criteria
    filtered_repositories = []
    for repo in repositories:
        if repo['size'] >= 3 and repo['owner']['type'] == 'User':
            # Check if owner's email is publicly visible on their profile
            owner_url = repo['owner']['url']
            owner_response = requests.get(owner_url, headers=headers)
            if owner_response.status_code == 200:
                owner_data = owner_response.json()
                owner_email = owner_data.get('email')
                if owner_email:
                    filtered_repositories.append({
                        'repository_name': repo['name'],
                        'owner_login': repo['owner']['login'],
                        'owner_email': owner_email
                    })

    # Print the filtered repositories
    for repo in filtered_repositories:
        print(f"Repository Name: {repo['repository_name']}")
        print(f"Owner: {repo['owner_login']}")
        print(f"Owner Email: {repo['owner_email']}")
        print("=" * 30)

else:
    print(f"Error fetching repositories: {response.status_code} - {response.reason}")