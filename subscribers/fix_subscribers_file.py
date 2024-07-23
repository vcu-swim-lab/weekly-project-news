import json
import re

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