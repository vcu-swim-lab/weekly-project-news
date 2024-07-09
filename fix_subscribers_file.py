import json
import re

def process_repo_names(data):
    for result in data['results']:
        repo_name = result['metadata'].get('repo_name', '')
        if repo_name:
            repo_name = re.sub(r'github\.com', 'github.com', repo_name, flags=re.IGNORECASE)
            if repo_name.lower().startswith('github.com'):
                repo_name = 'https://' + repo_name            
            result['metadata']['repo_name'] = repo_name

    return data

def main():
    # Read the JSON file
    with open('subscribers.json', 'r') as file:
        data = json.load(file)

    # Process the data
    processed_data = process_repo_names(data)

    # Write the processed data back to a new JSON file
    with open('subscribers.json', 'w') as file:
        json.dump(processed_data, file, indent=2)

    print("Processing complete.")

if __name__ == "__main__":
    main()