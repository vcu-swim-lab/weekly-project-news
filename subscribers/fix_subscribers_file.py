import json
import re
import requests

def process_repo_names(data):
    for subscriber in data['results']:
        repo_name = subscriber['metadata'].get('repo_name', '')
        slug_match = re.search(r'(?:github\.com/)?([^/]+/[^/]+)/?$', repo_name, re.IGNORECASE)
        if slug_match:
            slug = slug_match.group(1)
            subscriber['metadata']['repo_name'] = f'https://github.com/{slug}'
        else:
            # If they give something other than owner_name/repo_name, they're dumb
            pass
            
    return data

# Makes sure the repo is public and the link is actually a link
def check_repo(url):
    if ".com" not in url:
        print(f"Error: {url} does not contain a link.")
        return True
    try:
        response = requests.head(url, allow_redirects=True)
        if response.status_code == 404:
            print(f"Error 404: {url} not found.")
            return True
        else:
            print(f"{url} exists. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return True

def delete_problem_repos(data):
    for subscriber in data['results']:
        repo_url = subscriber['metadata'].get('repo_name', '')

        if check_repo(repo_url):
            subscriber = ''
            print(f"Deleted {repo_url} from subscribers.json")
        else:
            print(f"Repo link {repo_url} is valid.")

def main():
    # Read the JSON file
    with open('subscribers.json', 'r') as file:
        data = json.load(file)

    # Process the data
    processed_data = process_repo_names(data)

    delete_problem_repos(processed_data)

    # Write the processed data back to a new JSON file
    with open('subscribers.json', 'w') as file:
        json.dump(processed_data, file, indent=2)

    print("Processing complete.")

if __name__ == "__main__":
    main()