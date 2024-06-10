import json
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

load_dotenv('public.env')  

API_KEY = os.environ.get("OPENAI_KEY")

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

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

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

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

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

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

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

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

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

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

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

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

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

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

  return response['text'].lstrip('\n"')


# PRS 1
def summaries_open_pull_requests(repo):
  
  # PART 1: get the context
  if not repo.get("open_pull_requests"):
    context = "No open pull requests."
  else:
    context = json.dumps(repo["open_pull_requests"], indent=2).strip()

  # PART 2: get the question
  # TODO: should reflect the content, including what issue is about judging by title
  question = "Summarize the content of this data, representing the open pull requests in a GitHub repository"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

  return response['text'].lstrip('\n"')


# PRS 2
def summaries_closed_pull_requests(repo):
  
  # PART 1: get the context
  if not repo.get("closed_pull_requests"):
    context = "No closed pull requests."
  else:
    context = json.dumps(repo["closed_pull_requests"], indent=2).strip()

  # PART 2: get the question
  # TODO: should reflect the content, including what issue is about judging by title
  question = "Summarize the content of this data, representing the closed pull requests in a GitHub repository"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

  return response['text'].lstrip('\n"')


# PRS 3
def summaries_num_all_prs(repo):
  
  # PART 1: get the context
  if not repo.get("num_all_prs"):
    context = "No pull requests."
  else:
    context = json.dumps(repo["num_all_prs"], indent=2).strip()

  # PART 2: get the question
  # TODO: should reflect the content, including what issue is about judging by title
  question = "Summarize the content of this data, representing the number of open and closed pull requests in a GitHub repository"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

  return response['text'].lstrip('\n"')


# PRS 4
def summaries_num_open_prs(repo):
  
  # PART 1: get the context
  if not repo.get("num_open_prs"):
    context = "No open pull requests."
  else:
    context = json.dumps(repo["num_open_prs"], indent=2).strip()

  # PART 2: get the question
  # TODO: should reflect the content, including what issue is about judging by title
  question = "Summarize the content of this data, representing the number of open requests in a GitHub repository"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

  return response['text'].lstrip('\n"')


# PRS 5
def summaries_num_closed_prs(repo):
  
  # PART 1: get the context
  if not repo.get("num_closed_prs"):
    context = "No closed pull requests."
  else:
    context = json.dumps(repo["num_closed_prs"], indent=2).strip()

  # PART 2: get the question
  # TODO: should reflect the content, including what issue is about judging by title
  question = "Summarize the content of this data, representing the number of closed requests in a GitHub repository"

  # PART 3: generate the summary
  response = chain.invoke({"context": context, "question": question})

  return response['text'].lstrip('\n"')





if __name__ == '__main__':
  with open('github_data.json', 'r') as file:
    github_data = json.load(file)

  for repo in github_data:

    # output:
    # {
    #   "summaries_issues_open": "No unresolved problems in the GitHub repository.",
    #   "summaries_issues_closed": "No closed issues in the GitHub repository.",
    #   "summaries_num_all_open_issues": "Total number of open issues in GitHub repository is 26.",
    #   "summaries_num_weekly_open_issues": "Zero new open issues created this week.",
    #   "summaries_num_weekly_closed_issues": "Zero issues closed in the GitHub repository this week.",
    #   "summaries_issues_by_open_date": "The data represents a list of open issues in a GitHub repository related to the aio-libs/create-aio-app project. The issues are sorted by the amount of time they have been open, with the oldest issue being \"Once initial polish finished, update aiohttp docs and point users to this repository\" at 2086 days and the most recent being \"Let's put `create-aio-app` under the `aio-libs` org on PyPI\" at 172 days. The issues cover a range of topics such as documentation updates, deployment, testing, structure corrections, feature proposals, CI/CD improvements, and various bug fixes and enhancements.",
    #   "summaries_issues_by_number_of_comments": "The data represents a list of open issues in a GitHub repository, sorted by the number of comments each issue has. The issues range from adding parameters to a makefile, updating requirements, adding sections to the readme file, moving functionality from backend to frontend, adding authorization, creating issue templates, correcting project structure, tracking available ports, integrating Sentry support, deploying to Heroku, proposing new features, resolving permission denied errors, organizing projects under specific organizations, managing requirements, handling build dependencies, updating credentials in CI configurations, following conventional commit practices, and improving CI testing."
    # }

    summaries = {
      # "summaries_issues_open": summary_issues_open(repo),
      # "summaries_issues_closed": summary_issues_closed(repo),
      # "summaries_num_all_open_issues": summary_num_all_open_issues(repo),
      # "summaries_num_weekly_open_issues": summary_num_weekly_open_issues(repo),
      # "summaries_num_weekly_closed_issues": summary_num_weekly_closed_issues(repo),
      # "summaries_issues_by_open_date": summary_issues_by_open_date(repo),
      # "summaries_issues_by_number_of_comments": summary_issues_by_number_of_comments(repo),

      # "summaries_open_pull_requests": summaries_open_pull_requests(repo),
      # "summaries_closed_pull_requests": summaries_closed_pull_requests(repo),
      # "summaries_num_all_prs": summaries_num_all_prs(repo),
      # "summaries_num_open_prs": summaries_num_open_prs(repo),
      # "summaries_num_closed_prs": summaries_num_closed_prs(repo),
    }
    
  try:
      with open("newsletter_data.json", "w") as outfile:
          json.dump(summaries, outfile, indent=2)
          print(json.dumps(summaries, indent=4))
  except Exception as e:
      print(f"Error code: {e}")
