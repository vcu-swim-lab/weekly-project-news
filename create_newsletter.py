import json
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv('public.env')  

API_KEY = os.environ.get("OPENAI_KEY")

# models: https://platform.openai.com/docs/models
llm = ChatOpenAI(
  model_name="gpt-3.5-turbo", 
  temperature=0.9,
  openai_api_key=API_KEY
)

# Function that generates a summary of the project's PRs
# https://stackoverflow.com/questions/77316112/langchain-how-do-input-variables-work-in-particular-how-is-context-replaced
def generate_pull_requests_summary(context, question):
  
  # use a ConversationChain because LLMChain is deprecated
  conversation = ConversationChain(llm=llm, verbose=True)

  # use invoke because run is deprecated and takes only 1 argument
  response = conversation.invoke(input=question, context=context)

  print('1')
  # {'input': 'Be nice in 5 words or fewer', 'history': '', 'response': 'Treat others with kindness always.'}
  print(response)

  return response;


if __name__ == '__main__':
  with open('test_github_data.json', 'r') as file:
    github_data = json.load(file)

  for repo in github_data:
    context = "Some context"
    question = "Be nice in 5 words or fewer"
    summary = generate_pull_requests_summary(context, question)
    # repo['pull_requests_summary'] = pull_requests_summary

  # print(f"Pull Requests Summary:\n{pull_requests_summary}\n")

  print('2')
  # {'input': 'Be nice in 5 words or fewer', 'history': '', 'response': 'Treat others with kindness always.'}
  print(summary)

  # with open('newsletter_data.json', 'w') as file: 
  #   json.dump(github_data, file, indent=2)
