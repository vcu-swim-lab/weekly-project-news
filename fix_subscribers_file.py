import json
import re

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

def remove_specific_subscribers(data):
    emails_to_remove = [
        "kostadin@gmail.com",
        "stevenbui44@gmail.com",
        "shbui@ncsu.edu", 
        "novalski123@yopmail.com",
        "christian123@yopmail.com",
        "christian1234@yopmail.com",
        "imranm3@vcu.edu",
        "stevenbui91@gmail.com"
    ]
    data['results'] = [subscriber for subscriber in data['results'] if subscriber['email'] not in emails_to_remove]
    return data

def main():
    # Read the JSON file
    with open('subscribers.json', 'r') as file:
        data = json.load(file)

    # Round 1: Process the data
    processed_data = process_repo_names(data)

    # Round 2: Exclude REU subscribers
    processed_data = remove_specific_subscribers(processed_data)

    # Write the processed data back to a new JSON file
    with open('subscribers.json', 'w') as file:
        json.dump(processed_data, file, indent=2)

    print("Processing complete.")

if __name__ == "__main__":
    main()