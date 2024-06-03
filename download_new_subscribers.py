import requests
import os
from dotenv import load_dotenv

load_dotenv('public.env')  

headers = {
    "Authorization": f"Token {os.environ['BUTTONDOWN_API_KEY']}",
}

BASE_URL = "https://api.buttondown.email"
ENDPOINT = "/subscribers"
METHOD = "GET"

response = requests.request(METHOD, f"{BASE_URL}/v1{ENDPOINT}", headers=headers)

print(response.text)

# {
#   "results": [
#     {
#       "id": "e460635d-bd38-40c4-beb5-d4d635362d5f",
#       "email": "kostadin@gmail.com",                                              # email submitted from the buttondown website
#       "notes": "", 
#       "metadata": {                                                               # github repo submitted from the buttondown website
#         "repo_name": "https://github.com/tensorflow/tensorflow"
#       },
#       "tags": [],
#       "referrer_url": "https://buttondown.email/weekly-project-news",             # the buttondown website
#       "creation_date": "2024-05-16T19:23:06.309307Z",
#       "secondary_id": 1,
#       "subscriber_type": "regular",
#       "source": "api",
#       "utm_campaign": "",
#       "utm_medium": "",
#       "utm_source": "",
#       "referral_code": "whzzgj",
#       "avatar_url": "https://s.gravatar.com/avatar/605b50cc1af4045b13b866570149778a?s=100&d=404",
#       "stripe_customer_id": null,
#       "stripe_coupon": null,
#       "unsubscription_date": null,
#       "churn_date": null,
#       "unsubscription_reason": "",
#       "transitions": [
#         {
#           "date": "2024-05-16T19:23:25.068217Z",
#           "type": "regular"
#         }
#       ],
#       "ip_address": "128.172.49.129",
#       "last_open_date": null,
#       "last_click_date": null
#     }
#   ],
#   "next": null,
#   "previous": null,
#   "count": 1
# }