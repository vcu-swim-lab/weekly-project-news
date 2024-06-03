from googleapiclient import discovery
import json
import os
from dotenv import load_dotenv

load_dotenv('public.env')  

# TODO: we don't have the Perspective API key yet
API_KEY = os.environ.get("PERSPECTIVE_API_KEY")

# Function that gets text as a parameter and analyzes how toxic it is, returning
# a toxicity score
# from: https://developers.perspectiveapi.com/s/docs-sample-requests?language=en_US
def analyze_text(text):
  client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
  )
  
  analyze_request = {
    'comment': {'text': text},
    'requestedAttributes': {'TOXICITY': {}}
  }

  response = client.comments().analyze(body=analyze_request).execute()
  toxicity_score = response['attributeScores']['TOXICITY']['summaryScore']['value']

  print('score: ', toxicity_score)
  print(json.dumps(response, indent=2))

  return toxicity_score
  
if __name__ == '__main__':
  # with open('github_data.json', 'r') as file:
  #   data = json.load(file)

  # for item in data:
  #   # text = item['issue_text'] = item['pr_text'] + item['commit_messages']
  #   text = 'friendly greetings from steven'
  #   toxicity_score = analyze_text(text)
  #   item['toxicity_score'] = toxicity_score

  text = 'friendly greetings from steven'
  toxicity_score = analyze_text(text)