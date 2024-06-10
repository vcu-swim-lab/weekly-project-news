import json
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

from langchain.chains import LLMChain
from langchain.llms import OpenAI 
from langchain.prompts import PromptTemplate

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
def generate_pull_requests_summary(context, question):
# def generate_pull_requests_summary(prompt):
  
  # use a ConversationChain because LLMChain is deprecated
  # establishes a conversation connection
  # conversation = ConversationChain(llm=llm, verbose=True)

  print('a')
  print('Context: ', context)
  print('Question: ', question)
  print('b')


  prompt_template = "Context: {context}\nQuestion: {question}"
  PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

  print('c')
  print('Prompt: ', PROMPT)
  print('d')

  chain = LLMChain(llm=OpenAI(temperature=1.0, openai_api_key = os.environ.get("OPENAI_KEY")), prompt=PROMPT)

  # response = chain.invoke(question=question, input=PROMPT)
  response = chain.invoke({"context": context, "question": question})

  # use invoke because run is deprecated and takes only 1 argument
  # generates a response to an input question
  # response = conversation.invoke(input=question, context=context)
  # response = conversation.predict(input=prompt)
  # response = "not yet"

  return response;


if __name__ == '__main__':
  with open('github_data.json', 'r') as file:
    github_data = json.load(file)

  for repo in github_data:

    # case 1: there is no data (aka json field is [])
    if repo.get("num_all_open_issues") is None:
      context = "No data available."
    # case 2: there is data
    else:
      context = json.dumps(repo["num_all_open_issues"], indent=2)
      
    question = "Generate 10 words or fewer summarizing this data, representing the number of open issues"


    # print('a')
    # print(prompt)
    # print('b')

    # This is what the prompt looks like:
    # "Context :26
    # Question: Generate 10 words or fewer summarizing this data, representing the number of open issue"
    # prompt = f"Context: {context}\nQuestion: {question}"

    response = generate_pull_requests_summary(context, question)
    # response = generate_pull_requests_summary(prompt)

  print('Response:')

  print(response)
