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
# https://stackoverflow.com/questions/77316112/langchain-how-do-input-variables-work-in-particular-how-is-context-replaced
prompt_template = "Context: {context}\nQuestion: {question}\n"
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
llm=OpenAI(temperature=1.0, openai_api_key = API_KEY)
chain = LLMChain(llm=llm, prompt=PROMPT)


# ISSUES 1
def summary_issues_open(repo):
  
  # PART 1: get the context
  if not repo.get("issues_open"):
    context = "No open issues."
  else:
    context = json.dumps(repo["issues_open"], indent=2).strip()

  # PART 2: get the question
  question = "Generate 10 words or fewer summarizing this data, representing open issues in a GitHub repository"
  # question = "Summarize this data, representing the number of open issues"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})
  # response = {'context': '26', 'question': 'Generate 10 words or fewer summarizing this data, representing the number of open issues', 'text': 'There are 26 open issues in the data. '}

  # return response;
  return response['text'].lstrip('\n')


# ISSUES 2
def summary_issues_closed(repo):
  
  # PART 1: get the context
  if not repo.get("issues_closed"):
    context = "No closed issues."
  else:
    context = json.dumps(repo["issues_closed"], indent=2).strip()

  # PART 2: get the question
  question = "Generate 10 words or fewer summarizing this data, representing closed issues in a GitHub repository"
  # question = "Summarize this data, representing the number of open issues"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})
  # response = {'context': 'No closed issues.', 'question': 'Generate 10 words or fewer summarizing this data, representing closed issues in a GitHub repository', 'text': 'Summary: No recently closed issues found in repository.'}
  # print(response)

  # return response;
  return response['text'].lstrip('\n')



if __name__ == '__main__':
  with open('github_data.json', 'r') as file:
    github_data = json.load(file)

  for repo in github_data:

    summaries = {
       "summaries_issues_open": summary_issues_open(repo),
       "summaries_issues_closed": summary_issues_closed(repo)
    }
    
  print(json.dumps(summaries, indent=4))

  # try:
  #     with open("newsletter.json", "w") as outfile:
  #         json.dump(data, outfile, indent=2)
  #     print(f"Successfully added {PROJECT_NAME} to github_data.json")
  # except Exception as e:
  #     print(f"Error writing data for {PROJECT_NAME} to github_data.json")
  #     print(f"Error code: {e}")
