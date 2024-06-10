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
  temperature=1.0,
  openai_api_key=API_KEY
)

# Function that generates a summary of the project's PRs
# https://stackoverflow.com/questions/77316112/langchain-how-do-input-variables-work-in-particular-how-is-context-replaced
# def generate_pull_requests_summary(context, question):
def generate_pull_requests_summary(prompt):
  
  # use a ConversationChain because LLMChain is deprecated
  # establishes a conversation connection
  conversation = ConversationChain(llm=llm, verbose=True)

  # print('context: ', context)
  # print('question: ', question)

  # use invoke because run is deprecated and takes only 1 argument
  # generates a response to an input question
  response = conversation.invoke(input=question, context=context)

  return response;


if __name__ == '__main__':
  with open('github_data.json', 'r') as file:
    github_data = json.load(file)

  for repo in github_data:

    # case 1: there is np data (aka json field is [])
    if repo.get("num_all_open_issues") is None:
      context = "No data available."
    # case 2: there is data
    else:
      context = json.dumps(repo["num_all_open_issues"], indent=2)
      
    question = "Generate 10 words or fewer summarizing this data, representing the number of open issues"


    # This is what the prompt looks like:
    # "Context :26
    # Question: Generate 10 words or fewer summarizing this data, representing the number of open issue"
    prompt = f"Context: {context}\nQuestion: {question}"

    # response = generate_pull_requests_summary(context, question)
    response = generate_pull_requests_summary(prompt)

  print('Response:')

  # TODO: We need to change this prompt because ChatGPT is dumb as rocks I literally gave it a prompt
  # saying we have 26 open issues how many issues do we have and it keeps saying we have 5 issues I despise you
  print(response)

  # with open('newsletter_data.json', 'w') as file: 
  #   json.dump(github_data, file, indent=2)
