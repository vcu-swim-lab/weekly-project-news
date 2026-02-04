# This file sends the newsletter using the Buttondown API
# It logs each step of the sending process for debugging
# The script includes retry logic for API errors

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
logging.basicConfig(filename='send-newsletter.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# https://api.buttondown.com/v1/docs
headers = {
    "Authorization": f"Token {os.environ['BUTTONDOWN_API_KEY']}",
}
BASE_URL = "https://api.buttondown.com"

# Function 1: Create email with "imported" status (finalized, but won't auto-send)
def draft_email(subject, content):
    url = f"{BASE_URL}/v1/emails"
    data = {
        "subject": subject,
        "body": content,
        "status": "imported"  # Finalized status that can be sent programmatically
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code >= 200 and response.status_code < 300:
            response_data = response.json()
            logging.info(f"Successfully created email with subject: {subject}, ID: {response_data['id']}, status: {response_data.get('status')}")
            return response_data
        else:
            print(f"Error in draft_email() - Status: {response.status_code}")
            print(f"Response: {response.text}")
            logging.error(f"Error in draft_email() - Status code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error creating email: {str(e)}")
        logging.error(f"Exception in draft_email: {str(e)}")
        return None
    

# Function 2: Send finalized email to subscriber
def send_email_to_subscriber(subscriber_id, email_id):
    url = f"{BASE_URL}/v1/subscribers/{subscriber_id}/emails/{email_id}"
    
    print(f"Sending email {email_id} to subscriber {subscriber_id}")
    logging.info(f"Attempting to send email (ID: {email_id}) to subscriber (ID: {subscriber_id})")
    logging.info(f"API Call: POST {url}")

    try:
        response = requests.post(url, headers=headers, timeout=30)
        
        print(f"Sending response: {response.status_code}")
        logging.info(f"API Response: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            print("Successfully sent email")
            logging.info(f"Email (ID: {email_id}) successfully sent to subscriber (ID: {subscriber_id})")
            return response
        else:
            print("\nError in send_email_to_subscriber()")
            print(f"Failed to send email. Status code: {response.status_code}")
            print(f"Response: {response.text}\n")
            logging.error(f"Failed to send email to subscriber (ID: {subscriber_id}). Status code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        logging.error(f"Exception in send_email_to_subscriber: {str(e)}")
        return None

# "Main function"
logging.info("- - - - - - - - - - - - - - - - - - - - -")
logging.info("Starting newsletter sending process")

with open('subscribers.json', 'r') as file:
    subscribers_data = json.load(file)

# Track processed newsletters and emails
processed_newsletters = {}  # Maps newsletter_filepath to list of {email, subject, email_id}
processed_emails = set()  # Track which email addresses we've already sent to
subscriber_count = 0
successfully_sent = 0

for subscriber in subscribers_data['results']:
    if not subscriber.get('email') or subscriber.get('subscriber_type') != 'regular':
        error_message = f"Invalid subscriber: {subscriber.get('email', 'No email')} - Type: {subscriber.get('subscriber_type', 'Unknown')}"
        print(error_message)
        logging.error(error_message)
        continue

    subscriber_count += 1
    email = subscriber['email']
    

    # Check if we've already processed this email address
    if email in processed_emails:
        print(f"\n{'='*60}")
        print(f"SKIPPING DUPLICATE EMAIL: {email}")
        print(f"{'='*60}")
        print(f"This email address was already processed")
        logging.warning(f"Skipping duplicate email address: {email}")
        continue
    
    print(f"\n{'='*60}")
    print(f"PROCESSING SUBSCRIBER #{subscriber_count}: {email}")
    print(f"{'='*60}")
    logging.info(f"Processing subscriber #{subscriber_count}: {email}")

    github_repo = subscriber.get('metadata', {}).get('repo_name')
    if not github_repo:
        print(f"No repo found for: {email}")
        logging.error(f"No repo found for subscriber: {email}")
        continue

    # STEP 1: get the subscriber's newsletter file
    project_name = github_repo.split('github.com/')[-1].replace('/', '_')
    
    # Debug logging
    print(f"GitHub Repo: {github_repo}")
    print(f"Project Name: {project_name}")
    logging.info(f"GitHub repo: {github_repo}")
    logging.info(f"Project name: {project_name}")
    
    newsletter_filepath = f"newsletter_data/newsletter_{project_name}.txt"
    print(f"Looking for: {newsletter_filepath}")
    logging.info(f"Newsletter filepath: {newsletter_filepath}")
    
    if not os.path.exists(newsletter_filepath):
        print(f"Newsletter file NOT FOUND: {newsletter_filepath}")
        logging.error(f"No newsletter txt file found: {newsletter_filepath}")
        continue
    else:
        print(f"Newsletter file found")
        logging.info(f"Newsletter file found: {newsletter_filepath}")
    
    # Track newsletter file usage
    if newsletter_filepath not in processed_newsletters:
        processed_newsletters[newsletter_filepath] = []

    # STEP 2: get the content for the email
    with open(newsletter_filepath, 'r', encoding='utf-8') as newsletter_file:
        content = newsletter_file.read()
    
    # Validate content is not empty
    if not content or len(content.strip()) < 50:
        print(f"WARNING: Newsletter content is empty or too short ({len(content)} chars)")
        logging.warning(f"Newsletter content is empty or too short for {newsletter_filepath}: {len(content)} chars")
        continue
    else:
        print(f"Newsletter content loaded ({len(content)} chars)")
        logging.info(f"Newsletter content loaded: {len(content)} chars")

    # STEP 3: get the subject for the email
    name = github_repo.split('/')[-1]
    print(name)
    capitalized_name = name[0].upper() + name[1:]
    timestamp = datetime.now().strftime('%H:%M:%S')
    timestamp_from = (datetime.now() - timedelta(days=7)).strftime('%B %d, %Y')
    timestamp_to = datetime.now().strftime('%B %d, %Y')
    subject = f"Weekly GitHub Report for {capitalized_name}: {timestamp_from} - {timestamp_to} ({timestamp})"

    # STEP 4: Create the email with "imported" status (finalized)
    response = draft_email(subject, content)
    print(f"Response for creating email for {email}: {response}")
    if not response:
        print(f"Email not able to be created for: {email}")
        logging.error(f"Email not able to be created for: {email}")
        continue

    # STEP 5: Get the email ID and subscriber ID
    email_id = response['id']
    subscriber_id = subscriber['id']
    
    # Check for duplicate email IDs or subjects
    duplicate_found = False
    for prev_email in processed_newsletters[newsletter_filepath]:
        if prev_email['email_id'] == email_id:
            print(f"WARNING: Duplicate email ID detected: {email_id}")
            print(f"This email was already created for: {prev_email['subscriber_email']}")
            logging.warning(f"DUPLICATE EMAIL ID: {email_id} already used for {prev_email['subscriber_email']}")
            duplicate_found = True
            break
        if prev_email['subject'] == subject:
            print(f"WARNING: Duplicate subject detected: {subject}")
            print(f"This subject was already used for: {prev_email['subscriber_email']}")
            logging.warning(f"DUPLICATE SUBJECT: '{subject}' already used for {prev_email['subscriber_email']}")
            duplicate_found = True
            break
    
    if duplicate_found:
        print(f"Skipping send due to duplicate detection")
        logging.error(f"Skipping send to {email} due to duplicate email_id or subject")
        continue
    
    # Record this email's metadata
    processed_newsletters[newsletter_filepath].append({
        'subscriber_email': email,
        'subject': subject,
        'email_id': email_id
    })

    # STEP 6: Send the finalized email to the subscriber
    send_response = send_email_to_subscriber(subscriber_id, email_id)
    if send_response:
        print(f"Email sent to subscriber: {email}")
        logging.info(f"Email sent to subscriber: {email}")
        successfully_sent += 1
        # Mark this email address as processed
        processed_emails.add(email)
    else:
        print("Failed to send email to subscriber.")
        logging.error(f"Failed to send email to subscriber: {email}")

    print("\n\n\n")

# Summary
print(f"\n{'='*60}")
print(f"SENDING SUMMARY")
print(f"{'='*60}")
print(f"Total subscribers processed: {subscriber_count}")
print(f"Emails successfully sent: {successfully_sent}")
print(f"Unique newsletter files: {len(processed_newsletters)}")
print(f"\nNewsletter distribution:")
for newsletter_file, emails_sent in sorted(processed_newsletters.items()):
    print(f"{newsletter_file}")
    print(f"{len(emails_sent)} email(s) created and sent:")
    for email_info in emails_sent:
        print(f"- {email_info['subscriber_email']}")
        print(f"Subject: {email_info['subject']}")
        print(f"Email ID: {email_info['email_id']}")
print(f"{'='*60}\n")

logging.info(f"Newsletter sending process completed")
logging.info(f"Total subscribers processed: {subscriber_count}")
logging.info(f"Emails successfully sent: {successfully_sent}")