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
llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key = API_KEY)
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

  return response['text'].lstrip('\n"')


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

  return response['text'].lstrip('\n"')


# ISSUES 3
def summary_num_all_open_issues(repo):
  
  # PART 1: get the context
  if not repo.get("num_all_open_issues"):
    context = "No open issues."
  else:
    context = json.dumps(repo["num_all_open_issues"], indent=2).strip()

  # PART 2: get the question
  question = "Generate 10 words or fewer summarizing this data, representing the total number of open issues in a GitHub repository"
  # question = "Summarize this data, representing the number of open issues"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})
  # response = {'context': 'No closed issues.', 'question': 'Generate 10 words or fewer summarizing this data, representing closed issues in a GitHub repository', 'text': 'Summary: No recently closed issues found in repository.'}

  return response['text'].lstrip('\n"')


# ISSUES 4
def summary_num_weekly_open_issues(repo):
  
  # PART 1: get the context
  if not repo.get("num_weekly_open_issues"):
    context = "No open issues made this week."
  else:
    context = json.dumps(repo["num_weekly_open_issues"], indent=2).strip()

  # PART 2: get the question
  question = "Generate 10 words or fewer summarizing this data, representing the number of new open issues made this week in a GitHub repository"
  # question = "Summarize this data, representing the number of open issues"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})
  # response = {'context': 'No closed issues.', 'question': 'Generate 10 words or fewer summarizing this data, representing closed issues in a GitHub repository', 'text': 'Summary: No recently closed issues found in repository.'}

  return response['text'].lstrip('\n"')


# ISSUES 5
def summary_num_weekly_closed_issues(repo):
  
  # PART 1: get the context
  if not repo.get("num_weekly_closed_issues"):
    context = "No issues closed this week."
  else:
    context = json.dumps(repo["num_weekly_closed_issues"], indent=2).strip()

  # PART 2: get the question
  question = "Generate 10 words or fewer summarizing this data, representing the number of issues closed this week in a GitHub repository"
  # question = "Summarize this data, representing the number of open issues"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})
  # response = {'context': 'No closed issues.', 'question': 'Generate 10 words or fewer summarizing this data, representing closed issues in a GitHub repository', 'text': 'Summary: No recently closed issues found in repository.'}

  return response['text'].lstrip('\n"')


# ISSUES 6
def summary_issues_by_open_date(repo):
  
  # PART 1: get the context
  if not repo.get("issues_by_open_date"):
    context = "No open issues."
  else:
    context = json.dumps(repo["issues_by_open_date"], indent=2).strip()

  # PART 2: get the question
  # TODO: should reflect the content, including what issue is about judging by title
  question = "Summarize the content of this data, representing the open issues in a GitHub repository sorted by their time open"
  # question = "Summarize this data, representing the number of open issues"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})
  # response = {'context': 'No closed issues.', 'question': 'Generate 10 words or fewer summarizing this data, representing closed issues in a GitHub repository', 'text': 'Summary: No recently closed issues found in repository.'}

  return response['text'].lstrip('\n"')


# ISSUES 7
def summary_issues_by_number_of_comments(repo):
  
  # PART 1: get the context
  if not repo.get("issues_by_number_of_comments"):
    context = "No open issues."
  else:
    context = json.dumps(repo["issues_by_number_of_comments"], indent=2).strip()

  # PART 2: get the question
  # TODO: should reflect the content, including what issue is about judging by title
  question = "Summarize the content of this data, representing the open issues in a GitHub repository sorted by their number of comments"
  # question = "Summarize this data, representing the number of open issues"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})
  # response = {'context': 'No closed issues.', 'question': 'Generate 10 words or fewer summarizing this data, representing closed issues in a GitHub repository', 'text': 'Summary: No recently closed issues found in repository.'}

  return response['text'].lstrip('\n"')



if __name__ == '__main__':
  with open('github_data.json', 'r') as file:
    github_data = json.load(file)

  for repo in github_data:

    summaries = {
      "summaries_issues_open": summary_issues_open(repo),
      # "summaries_issues_closed": summary_issues_closed(repo),
      # "summaries_num_all_open_issues": summary_num_all_open_issues(repo),
      # "summaries_num_weekly_open_issues": summary_num_weekly_open_issues(repo),
      # "summaries_num_weekly_closed_issues": summary_num_weekly_closed_issues(repo),
      # "summaries_issues_by_open_date": summary_issues_by_open_date(repo),
      # "summaries_issues_by_number_of_comments": summary_issues_by_number_of_comments(repo),
    }
    
  print(json.dumps(summaries, indent=4))

  # try:
  #     with open("newsletter.json", "w") as outfile:
  #         json.dump(data, outfile, indent=2)
  #     print(f"Successfully added {PROJECT_NAME} to github_data.json")
  # except Exception as e:
  #     print(f"Error writing data for {PROJECT_NAME} to github_data.json")
  #     print(f"Error code: {e}")
