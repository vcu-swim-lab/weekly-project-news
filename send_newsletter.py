import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# https://api.buttondown.email/v1/docs
headers = {
    "Authorization": f"Token {os.environ['BUTTONDOWN_API_KEY']}",
}
BASE_URL = "https://api.buttondown.email"


# Function 1
# POST /emails: DRAFT an email, not sending it out yet but getting an email id
def draft_email(subject, content):
    url = f"{BASE_URL}/v1/emails"
    data = {
        "subject": subject,
        "body": content,
        "status": "about_to_send"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code >= 200 and response.status_code < 300:
        response_data = response.json()
        return response_data
    else:
        print("\nError in draft_email()")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}\n")
        return None
    

# Function 2
# POST /subscribers/{id_or_email}/emails/{email_id}: Send existing email to subscriber
def send_email_to_subscriber(subscriber_id, email_id):
    url = f"{BASE_URL}/v1/subscribers/{subscriber_id}/emails/{email_id}"
   
    response = requests.post(url, headers=headers)
    if response.status_code >= 200 and response.status_code < 300:

        # change email status from "about_to_send" to "sent"
        update_response = update_email_status(email_id)
        if update_response.status_code >= 200 and update_response.status_code < 300:
            return response
        else:
            print("\nError in send_email_to_subscriber()")
            print(f"Failed to send email. Status code: {response.status_code}")
            print(f"Response: {response.text}\n")
            return None
    else:
        print("\nError in send_email_to_subscriber()")
        print(f"Failed to send email. Status code: {response.status_code}")
        print(f"Response: {response.text}\n")
        return None
    

# Function 3: 
# PATCH /emails/{email_id}: Update email status to "sent"
def update_email_status(email_id):
    url = f"{BASE_URL}/v1/emails/{email_id}"
    data = {
        "subject": subject,
        "body": content,
        "status": "sent"
    }
    
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code >= 200 and response.status_code < 300:
        return response
    else:
        print(f"\nError in update_email_status() - Status code: {response.status_code}")
        print(f"Response: {response.text}\n")
        return None

    

# "Main function"
with open('test_subscribers.json', 'r') as file:
    subscribers_data = json.load(file)

for subscriber in subscribers_data['results']:
    email = subscriber['email']
    if email == 'kostadin@gmail.com':
        continue

    github_repo = subscriber.get('metadata', {}).get('repo_name')
    if not github_repo:
        print(f"No repo found for: {email}")
        continue

    # STEP 1: get the subscriber's markdown file from the folder
    project_name = github_repo.split('github.com/')[-1].replace('/', '_')
    newsletter_filepath = f"newsletter_data/newsletter_{project_name}.txt"
    if not os.path.exists(newsletter_filepath):
        print(f"No newsletter txt file found: {newsletter_filepath}")
        continue

    # STEP 2: get the content for the email
    with open(newsletter_filepath, 'r') as newsletter_file:
        content = newsletter_file.read()

    # STEP 3: get the subject for the email
    name = github_repo.split('/')[-1]
    capitalized_name = name[0].upper() + name[1:]
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    subject = f"Weekly GitHub Report for {capitalized_name} - {timestamp}"
    print('Subject: ', subject)

    # STEP 4: DRAFT the email using the content and subject to get an email ID (NOT sending it yet)
    response = draft_email(subject, content)
    if not response:
        print(f"Draft email not able to be made for: {email}")

    # STEP 5: SEND the email to the subscriber
    email_id = response['id']
    subscriber_id = subscriber['id']
    # send_response = send_email_to_subscriber(subscriber_id, email_id)
    # if send_response:
    #     print(f"Email sent to subscriber: {email}")
    # else:
    #     print("Failed to send email to subscriber.")

    print("\n\n\n")