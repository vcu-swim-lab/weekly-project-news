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


# Function 1
# POST /emails: DRAFT an email, not sending it out yet but getting an email id
def draft_email(subject, content):
    url = f"{BASE_URL}/v1/emails"
    data = {
        "subject": subject,
        "body": content,
        "status": "draft"
    }

    response = requests.post(url, headers=headers, json=data)
    print("1: draft_email")
    print('response.data:', response.json(), '\n')
    
    if response.status_code == 200:
        response_data = response.json()
        # print(f"Status: {response_data['status']}")
        # print(f"Email ID: {response_data['id']}")
        return response_data
    else:
        # print(f"Status code: {response.status_code}")
        # print(f"Response: {response.text}")
        return None
    

# Function 2
# GET /emails/{id}: Retrieves an email given its id
def get_draft_email(email_id):
    url = f"{BASE_URL}/v1/emails/{email_id}"
    
    response = requests.get(url, headers=headers)
    print('2: get_draft_email')
    print('response.data:', response.json(), '\n')

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get draft. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    

# Function 3
# POST /subscribers/{id_or_email}/emails/{email_id}: Send existing email to subscriber
def send_email_to_subscriber(subscriber_id, email_id, subject, content):
    url = f"{BASE_URL}/v1/subscribers/{subscriber_id}/emails/{email_id}"
    data = {
        "subject": subject,
        "body": content
    }
  
    response = requests.post(url, headers=headers, json=data)
    print('3: send_email_to_subscriber')
    print(response)

    if response.status_code == 201:
        return response.json()
    else:
        print(f"Failed to send email. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    

    

# "Main function"
with open('test_subscribers.json', 'r') as file:
    subscribers_data = json.load(file)

for subscriber in subscribers_data['results']:
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
            subject = f"Weekly GitHub Report for {github_repo.split('/')[-1].capitalize()}"

            # STEP 4: DRAFT the email first to get an email ID (NOT sending it)
            print('\n\n\na')
            print(content)
            print('b\n\n\n')
            response = draft_email(subject, content)
            # print('response:', response)

            if response:

              email_id = response['id']
              # print('email_id:', email_id)

              # STEP 5: GET the draft email itself
              draft_email = get_draft_email(email_id)
              # print(draft_email)

              if draft_email:
                  subscriber_id = subscriber['id']
                  # print('subscriber_id:', subscriber_id)

                  # STEP 6: SEND the email to the subscriber


                  # send_response = send_email_to_subscriber(subscriber_id, email_id, f"{draft_email['subject']} - {timestamp}", draft_email['body'])
                  # # print('send_response:', send_response)

                  # if send_response:
                  #     print(f"Email sent to subscriber. Email ID: {send_response['id']}")
                  # else:
                  #     print("Failed to send email to subscriber.")




            # STEP 5: get the subscriber ID and email ID for the API (/subscribers/{id_or_email}/emails/{email_id})
            # subscriber_id = subscriber['id']
            
            # if (subscriber_id):
            #     response = send_subscriber_email(subscriber_id, subject, content)
            #     print('response:', response)

            print("\n\n\n")
