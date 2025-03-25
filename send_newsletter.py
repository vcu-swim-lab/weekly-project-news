import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(
    filename='sending.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

# https://api.buttondown.email/v1/docs
headers = {
    "Authorization": f"Token {os.environ['BUTTONDOWN_API_KEY']}",
}
BASE_URL = "https://api.buttondown.com"


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

    if response.status_code >= 200 and response.status_code < 300:
        response_data = response.json()
        logging.info(f"Successfully drafted email with subject: {subject}")
        return response_data
    else:
        print("\nError in draft_email()")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}\n")
        logging.error(f"Error in draft_email() - Status code: {response.status_code}, Response: {response.text}")
        return None
    

# Function 2
# POST /subscribers/{id_or_email}/emails/{email_id}: Send existing email to subscriber
def send_email_to_subscriber(subscriber_id, email_id):
    url = f"{BASE_URL}/v1/subscribers/{subscriber_id}/emails/{email_id}"
    
    print(f"Sending email {email_id} to subscriber {subscriber_id}")
    logging.info(f"Attempting to send email (ID: {email_id}) to subscriber (ID: {subscriber_id})")

    response = requests.post(url, headers=headers)
    
    print(f"Sending response: {response.status_code}")
    
    if response.status_code >= 200 and response.status_code < 300:
        print("Successfully sent email")
        logging.info(f"Email (ID: {email_id}) successfully sent to subscriber (ID: {subscriber_id})")

        # Update email status from "about_to_send" to "imported"
        logging.info(f"Attempting to update email (ID: {email_id}) status to 'imported'")
        print(f"Attempting to update email (ID: {email_id}) status to 'imported'")
        update_response = update_email_status(email_id, "imported")
        if update_response and update_response.status_code >= 200 and update_response.status_code < 300:
            return response
        else:
            print("\nError updating email status after sending")
            print(f"Failed to update email status for email ID: {email_id}")
            logging.error(f"Failed to update email status for email ID: {email_id}")
            return None
    else:
        print("\nError in send_email_to_subscriber()")
        print(f"Failed to send email. Status code: {response.status_code}")
        print(f"Response: {response.text}\n")
        logging.error(f"Failed to send email to subscriber (ID: {subscriber_id}). Status code: {response.status_code}, Response: {response.text}")
        return None
    

# Function 3: 
# PATCH /emails/{email_id}: Update email status to "sent"

def update_email_status(email_id, status, max_retries=3, delay=5):
    url = f"{BASE_URL}/v1/emails/{email_id}"
    data = {
        "status": status
    }

    for attempt in range(1, max_retries + 1):
        response = requests.patch(url, headers=headers, json=data)

        if response.status_code >= 200 and response.status_code < 300:
            logging.info(f"Successfully updated email (ID: {email_id}) status to '{status}'")
            return response

        print(f"\nAttempt {attempt} - Error in update_email_status() - Status code: {response.status_code}")
        print(f"Response: {response.text}\n")
        logging.error(f"Attempt {attempt} - Error in update_email_status() - Status code: {response.status_code}, Response: {response.text}")

        if attempt < max_retries:
            time.sleep(delay)  # Wait before retrying
        else:
            logging.error(f"Failed to update email status after {max_retries} attempts.")
            return None


    

# "Main function"
logging.info("- - - - - - - - - - - - - - - - - - - - -")
logging.info("Starting newsletter sending process")

with open('subscribers.json', 'r') as file:
    subscribers_data = json.load(file)

for subscriber in subscribers_data['results']:
    if not subscriber.get('email') or subscriber.get('subscriber_type') != 'regular':
        error_message = f"Invalid subscriber: {subscriber.get('email', 'No email')} - Type: {subscriber.get('subscriber_type', 'Unknown')}"
        print(error_message)
        logging.error(error_message)
        continue

    email = subscriber['email']
    print('VALID: ', email)

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
    timestamp = datetime.now().strftime('%H:%M:%S')
    timestamp_from = (datetime.now() - timedelta(days=7)).strftime('%B %d, %Y')
    timestamp_to = datetime.now().strftime('%B %d, %Y')
    subject = f"Weekly GitHub Report for {capitalized_name}: {timestamp_from} - {timestamp_to} ({timestamp})"

    # STEP 4: DRAFT the email using the content and subject to get an email ID (NOT sending it yet)
    response = draft_email(subject, content)
    print(f"Response for drafting email for {email}: {response}")
    if not response:
        print(f"Draft email not able to be made for: {email}")
        logging.error(f"Draft email not able to be made for: {email}")
        continue


    # STEP 5: Get the email ID and subscriber ID
    email_id = response['id']
    subscriber_id = subscriber['id']

    # STEP 6: Update email status to "about_to_send"
    update_response = update_email_status(email_id, "about_to_send")
    if not update_response:
        print(f"Failed to update email status for: {email}")
        logging.error(f"Failed to update email status for: {email}")
        continue

    # STEP 7: Send the email to the subscriber
    send_response = send_email_to_subscriber(subscriber_id, email_id)
    if send_response:
        print(f"Email sent to subscriber: {email}")
        logging.info(f"Email sent to subscriber: {email}")
    else:
        print("Failed to send email to subscriber.")
        logging.error(f"Failed to send email to subscriber: {email}")

    # logging.info("Waiting for 60 seconds before processing next subscriber")
    # time.sleep(60)
    print("\n\n\n")

logging.info("Newsletter sending process completed")