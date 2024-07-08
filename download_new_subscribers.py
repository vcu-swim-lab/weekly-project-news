import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()  

headers = {
    "Authorization": f"Token {os.environ['BUTTONDOWN_API_KEY']}",
}

BASE_URL = "https://api.buttondown.email"
ENDPOINT = "/subscribers"
METHOD = "GET"

response = requests.request(METHOD, f"{BASE_URL}/v1{ENDPOINT}", headers=headers)

if response.status_code == 200:
  subscribers_data = response.json()
  filtered_data = []
  
  # Loop through and only pull out email and repo name
  for data in subscribers_data['results']:
    user_data = {
      'id': data['id'],
      'email': data['email'],
      'repo_name': data['metadata']['repo_name']
    }
    filtered_data.append(user_data)

  # save it to subscribers.json
  with open('subscribers.json', 'w') as file:
    json.dump(filtered_data, file, indent=2)

  print('Successfully saved to subscribers.json')
else:
  print(f"Error: {response.status_code} - {response.text}")