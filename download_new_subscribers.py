import requests
import os
from dotenv import load_dotenv
import json

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

  # save it to subscribers.json
  with open('subscribers.json', 'w') as file:
    json.dump(subscribers_data, file, indent=2)

  print('Successfully saved to subscribers.json')
else:
  print(f"Error: {response.status_code} - {response.text}")