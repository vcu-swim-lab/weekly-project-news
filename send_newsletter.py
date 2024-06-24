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
        "status": "about_to_send"
    }

    response = requests.post(url, headers=headers, json=data)
    print("1: draft_email")
    print('response.data:', response.json(), '\n')
    
    if response.status_code >= 200 and response.status_code < 300:
        response_data = response.json()
        return response_data
    else:
        print("\nError in draft_email()")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}\n")
        return None
    

# Function 3
# POST /subscribers/{id_or_email}/emails/{email_id}: Send existing email to subscriber
def send_email_to_subscriber(subscriber_id, email_id):

    url = f"{BASE_URL}/v1/subscribers/{subscriber_id}/emails/{email_id}"
    # data = {
    #     "subject": subject,
    #     "body": content,
    # }
    
    print('subscriber_id:', subscriber_id)
    print('email_id:', email_id)
    # print('subject:', data['subject'])
    # print('body:', data['body'])
  
    response = requests.post(url, headers=headers)
    print('3: send_email_to_subscriber')
    print('RESPONSE:', response, "\n")

    if response.status_code >= 200 and response.status_code < 300:

        update_response = update_email_status(email_id, "sent")
        print("update_response:", update_response)

        return response
    else:
        print("\nError in send_email_to_subscriber()")
        print(f"Failed to send email. Status code: {response.status_code}")
        print(f"Response: {response.text}\n")
        return None
    

# Function 4: Update email status to "sent"
def update_email_status(email_id, status):
    url = f"{BASE_URL}/v1/emails/{email_id}"
    data = {
        "subject": subject,
        "body": content,
        "status": "sent"
    }
    
    response = requests.patch(url, headers=headers, json=data)
    print(f'4: update_email_status - Status: {response.status_code}')
    print(f'RESPONSE: {response.text}\n')

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
    if subscriber['email'] == 'kostadin@gmail.com':
        continue

    email = subscriber['email']
    github_repo = subscriber.get('metadata', {}).get('repo_name')
    
    if github_repo:
        
        # STEP 1: get the subscriber's markdown file from the folder
        project_name = github_repo.split('github.com/')[-1].replace('/', '_')
        newsletter_filepath = f"newsletter_data/newsletter_{project_name}.txt"
        if os.path.exists(newsletter_filepath):
            
            # STEP 2: get the contents of the markdown txt file
            with open(newsletter_filepath, 'r') as newsletter_file:
                content = newsletter_file.read()

            # STEP 3: make the subject line for the email
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            subject = f"Weekly GitHub Report for {github_repo.split('/')[-1].capitalize()} - {timestamp}"

            # STEP 4: DRAFT the email first to get an email ID (NOT sending it)
            response = draft_email(subject, content)
            
            if response:
                email_id = response['id']
                subscriber_id = subscriber['id']

                # STEP 5: SEND the email to the subscriber
                send_response = send_email_to_subscriber(subscriber_id, email_id)
                if send_response:
                    print(f"Email sent to subscriber.")
                else:
                    print("Failed to send email to subscriber.")

            else:
                print('respnse does not exist')

            print("\n\n\n")