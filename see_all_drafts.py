import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Buttondown API setup
BUTTONDOWN_API_KEY = os.getenv('BUTTONDOWN_API_KEY')
BASE_URL = "https://api.buttondown.email"

headers = {
    "Authorization": f"Token {BUTTONDOWN_API_KEY}",
}

def get_email_drafts():
    url = f"{BASE_URL}/v1/emails"
    params = {
        # Choose one of these
        # "status": "about_to_send",
        # "status": "draft",
        # "status": "in_flight",
        "order": "-created"  # Get newest first
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        print('c')
        print(response.json())
        print('d')
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def display_drafts(drafts):
    if not drafts or 'results' not in drafts or len(drafts['results']) == 0:
        print("No drafts found.")
        return

    print('a')
    print('Drafts:')
    print(drafts)
    print('b')

    print(f"Found {len(drafts['results'])} draft(s):")
    for draft in drafts['results']:
        print(draft)
        print("-" * 30)



def delete_draft(draft_id):
    url = f"{BASE_URL}/v1/emails/{draft_id}"
    data = {
        "status": "deleted"
    }
    response = requests.patch(url, headers=headers, json=data)
    print('Response:', response)
    print('Response.json():', response.json())
    return response.status_code >= 200 and response.status_code < 300


def delete_all_drafts(drafts):
    total = len(drafts['results'])
    deleted = 0

    print("\nDeleting all drafts...")
    for draft in drafts['results']:
        if 'id' in draft:
            print('ID:', draft['id']);

            if delete_draft(draft['id']):
                deleted += 1
                print(f"Deleted draft: {draft.get('subject', 'No subject')}")
            else:
                print(f"Failed to delete draft: {draft.get('subject', 'No subject')}")
        else:
            print("Skipped draft with no ID")

    print(f"\nDeleted {deleted} out of {total} drafts.")



def main():
    print("Fetching email drafts from Buttondown...")
    drafts = get_email_drafts()
    if drafts:
        display_drafts(drafts)

        print('-')
        print('Deleting all drafts now')
        print('-')

        delete_all_drafts(drafts)

        print('Done')
    else:
        print("Error: drafts is null :(")
        

if __name__ == "__main__":
    main()