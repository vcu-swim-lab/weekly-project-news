import requests
import os
from dotenv import load_dotenv

load_dotenv()  

headers = {
    "Authorization": f"Token {os.environ['BUTTONDOWN_API_KEY']}",
}

BASE_URL = "https://api.buttondown.email"
ENDPOINT = "/subscribers"
METHOD = "GET"

response = requests.request(METHOD, f"{BASE_URL}/v1{ENDPOINT}", headers=headers)

print(response.text)