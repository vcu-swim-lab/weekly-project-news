import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

headers = {
    "Authorization": f"Token {os.environ['BUTTONDOWN_API_KEY']}",
}
BASE_URL = "https://api.buttondown.email"


# https://docs.buttondown.email/scheduling-emails-via-the-api
# https://api.buttondown.email/v1/docs


# POST /subscribers/{id_or_email}/emails/{email_id}: Send email to
# NOTE: This might mean sending an already existing email to a subscriber (do below first)
def send_email_to_subscriber(subscriber_id, subject, content):
    url = f"{BASE_URL}/subscribers/{subscriber_id}/emails"
    print('url:', url)
    data = {
        "subject": subject,
        "body": content
    }
    # 201: sends correctly (if subject different)
    # 400: if duplicate (error, cannot send)
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response)




# POST /emails: DRAFT an email, not sending it out yet but getting an email ID
def draft_newsletter(subject, content):
    url = f"{BASE_URL}/v1/emails"

    data = {
        "subject": subject,
        "body": content,
        "status": "draft"
    }

    response = requests.post(url, headers=headers, json=data)
    print('response:', response)
    print('response.data:', response.json())
    
    if response.status_code == 201:
        response_data = response.json()
        print(f"Status: {response_data['status']}")
        print(f"Email ID: {response_data['id']}")
        return response_data
    else:
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    

    

# "Main function"
with open('test_subscribers.json', 'r') as file:
    subscribers_data = json.load(file)

for subscriber in subscribers_data['results']:
    
    # TODO: remove this when no longer testing
    if subscriber['email'] == 'kostadin@gmail.com':
        continue

    email = subscriber['email']
    github_repo = subscriber.get('metadata', {}).get('repo_name')
    
    if github_repo:
        
        # STEP 1: get the subscriber's markdown file from the folder
        project_name = github_repo.split('github.com/')[-1].replace('/', '_')
        newsletter_filepath = f"newsletter_data/newsletter_{project_name}.txt"

        if os.path.exists(newsletter_filepath):
            
            # STEP 2: get the contents of the markdown file
            with open(newsletter_filepath, 'r') as newsletter_file:
                content = newsletter_file.read()

            # STEP 3: make the subject line for the email
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            subject = f"Weekly GitHub Report for {github_repo.split('/')[-1].capitalize()} - {timestamp}"

            # STEP 4: DRAFT the email first to get an email ID (NOT sending it)
            response = draft_newsletter(subject, content)
            print('response:', response)

            email_id = response['id']
            print('email_id:', email_id)




            # STEP 5: get the subscriber ID and email ID for the API (/subscribers/{id_or_email}/emails/{email_id})
            # subscriber_id = subscriber['id']
            
            # if (subscriber_id):
            #     response = send_subscriber_email(subscriber_id, subject, content)
            #     print('response:', response)

            print("\n\n\n")
