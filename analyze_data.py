from googleapiclient import discovery
import json

API_KEY = "TODO: Perspective API Key, might need to be in public.env"

# Function that gets text as a parameter and analyzes how toxic it is, returning
# a toxicity score
def analyze_text(text):

  # I got this from the Perspective API website's sample request :3
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