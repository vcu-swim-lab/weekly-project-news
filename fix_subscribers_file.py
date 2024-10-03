import json
import re
import requests

def process_repo_names(data):
    valid_subscribers = []
    for subscriber in data['results']:
        repo_name = subscriber['metadata'].get('repo_name', '')
        slug_match = re.search(r'(?:github\.com/)?([^/]+/[^/]+)/?$', repo_name, re.IGNORECASE)
        if slug_match:
            slug = slug_match.group(1)
            subscriber['metadata']['repo_name'] = f'https://github.com/{slug}'
            valid_subscribers.append(subscriber)
        else:
            # If they give something other than owner_name/repo_name, remove the subscriber
            print(f"Removing subscriber with invalid repo name: {repo_name}")
    
    data['results'] = valid_subscribers
    return data

# def remove_specific_subscribers(data):
#     emails_to_remove = [
#         "kostadin@gmail.com",
#         "stevenbui44@gmail.com",
#         "shbui@ncsu.edu", 
#         "novalski123@yopmail.com",
#         "christian123@yopmail.com",
#         "christian1234@yopmail.com",
#         "imranm3@vcu.edu",
#         "stevenbui91@gmail.com"
#     ]
#     data['results'] = [subscriber for subscriber in data['results'] if subscriber['email'] not in emails_to_remove]
#     return data

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
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return True

def delete_problem_repos(data):
    repos_deleted = 0
    index = 0
    
    while index < len(data['results']):
        repo_url = data['results'][index]['metadata'].get('repo_name', '')

        if check_repo(repo_url):
            data['results'].pop(index)
            print(f"Deleted {repo_url} from subscribers.json as the link was not valid.")
            repos_deleted += 1
            continue
        else:
            print(f"Repo link {repo_url} is valid.")
            index += 1
            
        
    data['count'] = data['count'] - repos_deleted
    print(f"{repos_deleted} repositories deleted from subscribers.json")

def main():
    # Read the JSON file
    with open('subscribers.json', 'r') as file:
        data = json.load(file)

    # Round 1: Process the data
    processed_data = process_repo_names(data)
    
    delete_problem_repos(processed_data)

    # Round 2: Remove private/fake/non-GitHub repos
    delete_problem_repos(processed_data)

    # Write the processed data back to a new JSON file
    with open('subscribers.json', 'w') as file:
        json.dump(processed_data, file, indent=2)

    print("Processing complete.")

if __name__ == "__main__":
    main()