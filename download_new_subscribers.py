# This file interacts with the Buttondown API to download all of the subscribers for the newsletter
# Outputs a JSON file

import requests
import os
import json
from dotenv import load_dotenv

def download_subscribers(api_key=None):
    load_dotenv()
    
    # Use provided API key or get from environment
    api_key = api_key or os.environ.get('BUTTONDOWN_API_KEY')
    if not api_key:
        print("Invalid API key")
        return False, {"error": "No API key provided"}
    
    headers = {
        "Authorization": f"Token {api_key}",
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
        return True, subscribers_data
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False, {"status_code": response.status_code, "response_text": response.text}


if __name__ == "__main__":
    download_subscribers()