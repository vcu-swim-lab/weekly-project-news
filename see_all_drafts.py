import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# https://api.buttondown.email/v1/docs#/
# Buttondown API setup
BUTTONDOWN_API_KEY = os.getenv('BUTTONDOWN_API_KEY')
BASE_URL = "https://api.buttondown.email"

headers = {
    "Authorization": f"Token {BUTTONDOWN_API_KEY}",
}

# 1: Get all drafts
def get_drafts():
    url = f"{BASE_URL}/v1/emails"
    params = {
        "status": "draft",
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
    


# 2: Get all about_to_sends
def get_about_to_sends():
    url = f"{BASE_URL}/v1/emails"
    params = {
        "status": "about_to_send",
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
    

    
# 3: Get all scheduleds
def get_scheduleds():
    url = f"{BASE_URL}/v1/emails"
    params = {
        "status": "scheduled",
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
    


# 4: Get all in_flights
def get_in_flights():
    url = f"{BASE_URL}/v1/emails"
    params = {
        "status": "in_flight",
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
    


# 4.5: Get all sents
def get_sents():
    url = f"{BASE_URL}/v1/emails"
    params = {
        "status": "sent",
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
    


# 4.75: Get all importeds
def get_importeds():
    url = f"{BASE_URL}/v1/emails"
    params = {
        "status": "imported",
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


# 4.875: Get all importeds
def get_deleteds():
    url = f"{BASE_URL}/v1/emails"
    params = {
        "status": "deleted",
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





# 5: Print out all drafts
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





# 6: Delete all drafts
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

# 6.1: Delete a specific draft
def delete_draft(draft_id):
    url = f"{BASE_URL}/v1/emails/{draft_id}"
    data = {
        "status": "deleted"
    }
    response = requests.patch(url, headers=headers, json=data)
    print('Response:', response)
    print('Response.json():', response.json())
    return response.status_code >= 200 and response.status_code < 300





# Main
def main():
    print()

    # # 1: Get drafts
    drafts = get_drafts()
    if drafts:
        display_drafts(drafts)
        # delete_all_drafts(drafts)
    else:
        print("Error: drafts is null :(")

    # # 2: Get about_to_sends
    # about_to_sends = get_about_to_sends()
    # if about_to_sends:
    #     display_drafts(about_to_sends)
    #     # delete_all_drafts(about_to_sends)
    # else:
    #     print("Error: about_to_sends is null :(")

    # # 3: Get scheduleds
    # scheduleds = get_scheduleds()
    # if scheduleds:
    #     display_drafts(scheduleds)
    #     # delete_all_drafts(scheduleds)
    # else:
    #     print("Error: scheduleds is null :(")

    # # 4: Get in_flights
    # in_flights = get_in_flights()
    # if in_flights:
    #     display_drafts(in_flights)
    #     # delete_all_drafts(in_flights)
    # else:
    #     print("Error: in_flights is null :(")

    # # 4: Get in_flights
    # sents = get_sents()
    # if sents:
    #     display_drafts(sents)
    #     # delete_all_drafts(in_flights)
    # else:
    #     print("Error: sents is null :(")

    # 5: Get importeds
    # importeds = get_importeds()
    # if importeds:
    #     display_drafts(importeds)
    #     # delete_all_drafts(in_flights)
    # else:
    #     print("Error: importeds is null :(")


    # # 6: Get deleteds
    # deleteds = get_deleteds()
    # if deleteds:
    #     display_drafts(deleteds)
    #     # delete_all_drafts(in_flights)
    # else:
    #     print("Error: deleteds is null :(")

    # delete_draft('f9da174c-cb0c-42e2-a16b-64fa93db41c4')
        

if __name__ == "__main__":
    main()