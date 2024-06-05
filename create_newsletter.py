import json
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI
import os
from dotenv import load_dotenv

load_dotenv('public.env')  

API_KEY = os.environ.get("OPENAI_KEY")

# TODO: not sure what model, https://platform.openai.com/docs/models
llm = OpenAI(api_key=API_KEY, model_name="text-davinci-003")

# Function that generates a summary of the project's issues, returning a
# summary that can be put in the newsletter
def generate_issues_summary(issues, toxicity_score):
  template = """
  Given the following issues for a project:
  Issues: {issues}
  Toxicity Score: {toxicity_score}

  Generate a concise summary of the notable issues and conversations from the past week.
  """

  prompt = PromptTemplate(
    input_variables=["issues", "toxicity_score"],
    template=template,
  )

  chain = LLMChain(llm=llm, prompt=prompt)
  summary = chain.run(issues=issues, toxicity_score=toxicity_score)
  return summary

# Function that generates a summary of the project's PRs, returning a
# summary that can be put in the newsletter
def generate_pull_requests_summary(pull_requests, toxicity_score):
  template = """
  Given the following pull requests for a project:
  Pull Requests: {pull_requests}
  Toxicity Score: {toxicity_score}

  Generate a concise summary of the notable pull requests and discussions from the past week.
  """

  prompt = PromptTemplate(
    input_variables=["pull_requests", "toxicity_score"],
    template=template,
  )

  chain = LLMChain(llm=llm, prompt=prompt)
  summary = chain.run(pull_requests=pull_requests, toxicity_score=toxicity_score)
  return summary

# Function that generates a summary of the project's commit messages, 
# returning a summary that can be put in the newsletter
def generate_commit_messages_summary(commit_messages):
  template = """
  Given the following commit messages for a project:
  Commit Messages: {commit_messages}

  Generate a concise summary of the commit activity from the past week.
  """

  prompt = PromptTemplate(
    input_variables=["commit_messages"],
    template=template,
  )

  chain = LLMChain(llm=llm, prompt=prompt)
  summary = chain.run(commit_messages=commit_messages)
  return summary


if __name__ == '__main__':
  # with open('analyzed_data.json', 'r') as file:
  #   data = json.load(file)

  # for item in data:
  #   issues_summary = generate_issues_summary(item['issue_text'], item['toxicity_score'])
  #   pull_requests_summary = generate_pull_requests_summary(item['pr_text'], item['toxicity_score'])
  #   commit_messages_summary = generate_commit_messages_summary(item['commit_messages'])

  #   item['issues_summary'] = issues_summary
  #   item['pull_requests_summary'] = pull_requests_summary
  #   item['commit_messages_summary'] = commit_messages_summary

  # with open('newsletter_data.json', 'w') as file:
  #   json.dump(data, file)

  issues_summary = generate_issues_summary('this is testing issue data', 0.1)
  pull_requests_summary = generate_pull_requests_summary('this is testing PR data', 0.1)
  commit_messages_summary = generate_commit_messages_summary('this is testing commit data', 0.1)