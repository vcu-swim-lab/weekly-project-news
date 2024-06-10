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

# TODO: when you add "model_name="gpt-3.5-turbo" to llm, the API key is not recognized
prompt_template = "Context: {context}\nQuestion: {question}\n"
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
llm=OpenAI(temperature=1.0, openai_api_key = API_KEY)
chain = LLMChain(llm=llm, prompt=PROMPT)


# Function that generates a summary of the project's PRs
# https://stackoverflow.com/questions/77316112/langchain-how-do-input-variables-work-in-particular-how-is-context-replaced
def summary_num_all_open_issues(repo):
  
  # case 1: there is no data (aka json field is [])
  if repo.get("num_all_open_issues") is None:
    context = "No data available."
  # case 2: there is data
  else:
    context = json.dumps(repo["num_all_open_issues"], indent=2)

  question = "Generate 10 words or fewer summarizing this data, representing the number of open issues"
  # question = "Summarize this data, representing the number of open issues"

  # response = chain.invoke({"context": context, "question": question})
  response = {'context': '26', 'question': 'Generate 10 words or fewer summarizing this data, representing the number of open issues', 'text': 'Answer: There are 26 open issues in the data. '}

  return response;


if __name__ == '__main__':
  with open('github_data.json', 'r') as file:
    github_data = json.load(file)

  for repo in github_data:

    response = summary_num_all_open_issues(repo)
    summary_num_all_open_issues = response['text']
    
  print('Summary of all open issues:')
  print(summary_num_all_open_issues)
