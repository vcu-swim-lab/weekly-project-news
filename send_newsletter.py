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
# TODO: Basic Plan allows you to schedule emails


# /subscribers/{id_or_email}/emails/{email_id}: Send email to
#   NOTE: This might mean sending an already existing email to a subscriber (BOOOOOOO)
def send_subscriber_email(subscriber_id, subject, content):
    url = f"{BASE_URL}/subscribers/{subscriber_id}/emails"
    print('url:', url)
    data = {
        "subject": subject,
        "body": content
    }

    response = requests.get(BASE_URL + "/subscribers/stevenbui44@gmail.com", headers=headers, data=json.dumps(data))
    print(response)


    # 201: sends correctly (if subject different)
    # 400: if duplicate (error, cannot send)
    # response = requests.post(url, headers=headers, data=json.dumps(data))
    # print(response)


    # if response.status_code == 201:
    #     response_data = response.json()

    #     print('response_data:', response_data)

    #     print(f"Email queued successfully for {email}")
    #     print(f"Status: {response_data['status']}")
    #     print(f"Email ID: {response_data['id']}")
    #     return response_data
    # else:
    #     print(f"Failed to queue email for {email}")
    #     print(f"Status code: {response.status_code}")
    #     print(f"Response: {response.text}")
    #     return None
    

    

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

            # STEP 4: get the subscriber ID and email ID for the API (/subscribers/{id_or_email}/emails/{email_id})
            subscriber_id = subscriber['id']
            
            if (subscriber_id):
                response = send_subscriber_email(subscriber_id, subject, content)
                print('response:', response)

            # response = send_newsletter(email, subject, content)

            # print(response)
            # print('code:', response['code'])
            # print('detail:', response['detail'])


            # status_code, response_text = send_newsletter(email, subject, content)
    #         if status_code == 201:
    #             print(f"Successfully sent newsletter to {email} for repository {github_repo}")
    #         else:
    #             print(f"Failed to send newsletter to {email} for repository {github_repo}")
    #             print(f"Error: {status_code} - {response_text}")
    #     else:
    #         print(f"Newsletter file {newsletter_filepath} not found for repository {github_repo}")
    # else:
    #     print(f"No GitHub repository specified for subscriber {email}")