import json
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
# from langchain.chains import LLMChain
from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate

load_dotenv()  

API_KEY = os.environ.get("OPENAI_KEY")

# https://stackoverflow.com/questions/77316112/langchain-how-do-input-variables-work-in-particular-how-is-context-replaced
prompt_template = "Context: {context}\nQuestion: {question}\n"
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key = API_KEY)
chain = PROMPT | llm


# Generates the summary using ChatGPT given any context and question (prompt template above)
def generate_summary(context, question):
    response = chain.invoke({"context": context, "question": question})
    return response.content


# ISSUES 1
def summary_issues_open(repo):
  context = "No open issues." if not repo.get("issues_open") else json.dumps(repo["issues_open"], indent=2).strip()
  question = "Generate 10 words or fewer summarizing this data, representing open issues in a GitHub repository"
  return generate_summary(context, question)

# ISSUES 2
def summary_issues_closed(repo):
  context = "No closed issues." if not repo.get("issues_closed") else json.dumps(repo["issues_closed"], indent=2).strip()
  question = "Generate 10 words or fewer summarizing this data, representing closed issues in a GitHub repository"
  return generate_summary(context, question)

# ISSUES 3
def summary_num_all_open_issues(repo):
  context = "No open issues." if not repo.get("num_all_open_issues") else json.dumps(repo["num_all_open_issues"], indent=2).strip()
  question = "Generate 10 words or fewer summarizing this data, representing the total number of open issues in a GitHub repository"
  return generate_summary(context, question)

# ISSUES 4
def summary_num_weekly_open_issues(repo):
  context = "No open issues made this week." if not repo.get("num_weekly_open_issues") else json.dumps(repo["num_weekly_open_issues"], indent=2).strip()
  question = "Generate 10 words or fewer summarizing this data, representing the number of new open issues made this week in a GitHub repository"
  return generate_summary(context, question)

# ISSUES 5
def summary_num_weekly_closed_issues(repo):
  context = "No issues closed this week." if not repo.get("num_weekly_closed_issues") else json.dumps(repo["num_weekly_closed_issues"], indent=2).strip()
  question = "Generate 10 words or fewer summarizing this data, representing the number of issues closed this week in a GitHub repository"
  return generate_summary(context, question)

# ISSUES 6
def summary_issues_by_open_date(repo):
  context = "No open issues." if not repo.get("issues_by_open_date") else json.dumps(repo["issues_by_open_date"], indent=2).strip()
  question = "Summarize the content of this data, representing the open issues in a GitHub repository sorted by their time open"
  return generate_summary(context, question)

# ISSUES 7
def summary_issues_by_number_of_comments(repo):
  context = "No open issues." if not repo.get("issues_by_number_of_comments") else json.dumps(repo["issues_by_number_of_comments"], indent=2).strip()
  question = "Summarize the content of this data, representing the open issues in a GitHub repository sorted by their number of comments"
  return generate_summary(context, question)



# PRS 1
def summary_open_pull_requests(repo):
  context = "No open pull requests." if not repo.get("open_pull_requests") else json.dumps(repo["open_pull_requests"], indent=2).strip()
  question = "Summarize the content of this data, representing the open pull requests in a GitHub repository"
  return generate_summary(context, question)

# PRS 2
def summary_closed_pull_requests(repo):
  context = "No closed pull requests." if not repo.get("closed_pull_requests") else json.dumps(repo["closed_pull_requests"], indent=2).strip()
  question = "Summarize the content of this data, representing the closed pull requests in a GitHub repository"
  return generate_summary(context, question)

# PRS 3
def summary_num_all_prs(repo):
  context = "No pull requests." if not repo.get("num_all_prs") else json.dumps(repo["num_all_prs"], indent=2).strip()
  question = "Summarize the content of this data, representing the number of open and closed pull requests in a GitHub repository"
  return generate_summary(context, question)

# PRS 4
def summary_num_open_prs(repo):
  context = "No open pull requests." if not repo.get("num_open_prs") else json.dumps(repo["num_open_prs"], indent=2).strip()
  question = "Summarize the content of this data, representing the number of open requests in a GitHub repository"
  return generate_summary(context, question)

# PRS 5
def summary_num_closed_prs(repo):
  context = "No closed pull requests." if not repo.get("num_closed_prs") else json.dumps(repo["num_closed_prs"], indent=2).strip()
  question = "Summarize the content of this data, representing the number of closed requests in a GitHub repository"
  return generate_summary(context, question)



# COMMITS 1
def summary_commits(repo):
  context = "No commits." if not repo.get("commits") else json.dumps(repo["commits"], indent=2).strip()
  question = "Summarize the content of this data, representing all of the commits in a GitHub repository"
  return generate_summary(context, question)

# COMMITS 2
def summary_num_commits(repo):
  context = "No commits." if not repo.get("num_commits") else json.dumps(repo["num_commits"], indent=2).strip()
  question = "Summarize the content of this data, representing the number of commits in a GitHub repository"
  return generate_summary(context, question)



# CONTRIBUTORS 1
def summary_new_contributors(repo):
  context = "No new contributors this week." if not repo.get("new_contributors") else json.dumps(repo["new_contributors"], indent=2).strip()
  question = "Summarize the content of this data, representing the number of new contributors in a GitHub repository"
  return generate_summary(context, question)

# CONTRIBUTORS 2
def summary_contributed_this_week(repo):
  context = "No contributors this week." if not repo.get("contributed_this_week") else json.dumps(repo["contributed_this_week"], indent=2).strip()
  question = "Summarize the content of this data, representing the number of contributors this week in a GitHub repository"
  return generate_summary(context, question)

# CONTRIBUTORS 3
def summary_active_contributors(repo):
  context = "No active contributors." if not repo.get("active_contributors") else json.dumps(repo["active_contributors"], indent=2).strip()
  question = "Summarize the content of this data, representing the number of active contributors in a GitHub repository"
  return generate_summary(context, question)
  


if __name__ == '__main__':
  github_directory = 'github_data'
  newsletter_directory = 'newsletter_data'
  
  if not os.path.exists(newsletter_directory):
    os.makedirs(newsletter_directory)
    
  for filename in os.listdir(github_directory):
    if filename.startswith('github') and filename.endswith('.json'):
      filepath = os.path.join(github_directory, filename)

      with open(filepath, 'r') as file:
        repo = json.load(file)
        summaries = {
          "summaries_issues_open": summary_issues_open(repo),
          "summaries_issues_closed": summary_issues_closed(repo),
          "summaries_num_all_open_issues": summary_num_all_open_issues(repo),
          "summaries_num_weekly_open_issues": summary_num_weekly_open_issues(repo),
          "summaries_num_weekly_closed_issues": summary_num_weekly_closed_issues(repo),
          "summaries_issues_by_open_date": summary_issues_by_open_date(repo),
          "summaries_issues_by_number_of_comments": summary_issues_by_number_of_comments(repo),

          "summaries_open_pull_requests": summary_open_pull_requests(repo),
          "summaries_closed_pull_requests": summary_closed_pull_requests(repo),
          "summaries_num_all_prs": summary_num_all_prs(repo),
          "summaries_num_open_prs": summary_num_open_prs(repo),
          "summaries_num_closed_prs": summary_num_closed_prs(repo),

          "summaries_commits": summary_commits(repo),
          "summaries_num_commits": summary_num_commits(repo),

          "summaries_new_contributors": summary_new_contributors(repo),
          "summaries_contributed_this_week": summary_contributed_this_week(repo),
          "summaries_active_contributors": summary_active_contributors(repo)
        }

        # get the project name (ex. tensorflow_tensorflow)
        project_name = filename.split('github_')[1].rsplit('.json')[0]

        # get the file name in the output folder (ex. newsletter_tensorflow_tensorflow)
        newsletter_filename = os.path.join(newsletter_directory, f"newsletter_{project_name}.json")

        try:
            with open(newsletter_filename, "w") as outfile:
                json.dump(summaries, outfile, indent=2)
            print(f"Successfully added {project_name} to {newsletter_filename}")
        except Exception as e:
            print(f"Error writing {project_name} to {newsletter_filename}")
            print(f"Error code: {e}")
