import json
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate

load_dotenv()  

API_KEY = os.environ.get("OPENAI_KEY")

# https://stackoverflow.com/questions/77316112/langchain-how-do-input-variables-work-in-particular-how-is-context-replaced
prompt_template = "Instructions: {instructions}\nJSON data: {data}\n"
PROMPT = PromptTemplate(template=prompt_template, input_variables=["instructions", "data"])
llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key = API_KEY, max_tokens=50)
chain = PROMPT | llm


# Generates the summary using ChatGPT given any context and question (prompt template above)
def generate_summary(instructions, data):
    response = chain.invoke({"instructions": instructions, "data": data})
    return response.content


# # 1 - ISSUES: Statistics
# def issues_statistics(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
#   Create the newsletter section describing all of the total open issues, issues opened this week, and issues closed this week using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (numbers). If you do not know something, say you do not know instead of making something up. 
#   Follow this structure: 
#   Use '## Statistics' as the main header. 
#   Use '### Total Open Issues' for the subheading.
#   A bullet point with 2-3 sentences giving a description of the total open issues this week. 
#   Use '### Issues Opened This Week' for the subheading.
#   A bullet point with 2-3 sentences giving a description of the issues opened this week.
#   Use '### Issues Closed This Week' for the subheading. 
#   A bullet point with 2-3 sentences giving a description of the issues closed this week. 
#   Use '### All Open Issues' for the subheading.
#   A bullet point with 2-3 sentences giving a description of each open issue based on comments, body, and issue title. If there are more than 10 issues, cluster some bullet points together so there are at most 10 bullet points.
#   Show the output with markdown tags in a code block. Do not just give regular output."""

#   data = {
#     "num_all_open_issues": repo['num_all_open_issues'],
#     "num_weekly_open_issues": repo['num_weekly_open_issues'],
#     "num_weekly_closed_issues": repo['num_weekly_closed_issues'],
#     "open_issues": repo['open_issues']
#   }

#   return generate_summary(instructions, data).strip()


# 2 - ISSUES: Active Open Issues in the Past Week
# def issues_active_open_issues_in_the_past_week(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
#   Create the newsletter section describing all active issues opened this week (indicated by number of comments) using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (title, number of comments). If you do not know something, say you do not know instead of making something up. 
#   Follow this structure: 
#   Use '## Active Open Issues in the Past Week' as the main header. 
#   Use '### Issue: ' + (title of issue) for each subheading. 
#   A bullet point giving a link to the active issue, then a bullet point with 2-3 sentences giving a description of each active issue. If there are more than 10 issues, cluster some issues together so there are at most 10 bullet points.
#   Show the output with markdown tags in a code block. Do not just give regular output."""

#   data = repo['issues_by_number_of_comments']

#   return generate_summary(instructions, data).strip()


# # 3 - ISSUES: Quiet Open Issues Currently
# def issues_quiet_open_issues_currently(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
#   Create the newsletter section describing all issues that have gone quiet (indicated by time still opened) using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (title, time open). If you do not know something, say you do not know instead of making something up. 
#   Follow this structure: 
#   Use '## Quiet Open Issues Currently' as the main header. 
#   Use '### Issue: ' + (title of issue) for each subheading. 
#   A bullet point giving a link to the open issue, then a bullet point with 2-3 sentences giving a description of each open issue. If there are more than 10 issues, only list the top 10 oldest open issues.
#   Show the output with markdown tags in a code block. Do not just give regular output."""

#   data = repo['issues_by_open_date']
  
#   return generate_summary(instructions, data).strip()


# # 4 - ISSUES: Closed Issues
# def issues_closed_issues(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
#   Create the newsletter section describing all issues that have been closed this week using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (title, body, any comments). If you do not know something, say you do not know instead of making something up. 
#   Follow this structure: 
#   Use '## Closed Issues' as the main header. 
#   Use '### Issue: ' + (title of issue) for each subheading. 
#   A bullet point giving a link to the closed issue, then a bullet point with 2-3 sentences giving a description of each closed issue. If there are more than 10 issues, only list 10 issues.
#   Show the output with markdown tags in a code block. Do not just give regular output."""

#   data = repo['issues_closed']

#   return generate_summary(instructions, data).strip()


# # 5 - PULL REQUESTS: Statistics
# def pull_requests_statistics(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
#   Create the newsletter section describing all of the open and closed pull requests this week using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (title, body). If you do not know something, say you do not know instead of making something up. 
#   Follow this structure: 
#   Use '## Statistics' as the main header. 
#   Use '### Total Open and Closed PRs' for the subheading. 
#   A bullet point with 2-3 sentences giving a description of the total open and closed issues this week. 
#   Use '### PRs Opened This Week' for the subheading. 
#   A bullet point with 2-3 sentences giving a description of the PRs opened this week. 
#   Use '### PRs Closed This Week' for the subheading. 
#   A bullet point with 2-3 sentences giving a description of the PRs closed this week. 
#   Show the output with markdown tags in a code block. Do not just give regular output."""

#   data = {
#     "num_all_prs": repo['num_all_prs'],
#     "num_open_prs": repo['num_open_prs'],
#     "num_closed_prs": repo['num_closed_prs']
#   }

#   return generate_summary(instructions, data).strip()


# # 6 - PULL REQUESTS: Open PRS
# def pull_requests_open_prs(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
#   Create the newsletter section describing all of the open pull requests this week using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (title, body). If you do not know something, say you do not know instead of making something up. 
#   Follow this structure: 
#   Use '## Open PRs' as the main header. 
#   Use '### PR: ' + (title of pull request) for each subheading. 
#   A bullet point with 2-3 sentences giving a description of each open PR. If there are more than 10 PRs, cluster some PRs together so there are at most 10 bullet points.
#   Show the output with markdown tags in a code block. Do not just give regular output."""

#   data = repo['open_pull_requests']

#   return generate_summary(instructions, data).strip()


# # 7 - PULL REQUESTS: Closed PRs
# def pull_requests_closed_prs(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
#   Create the newsletter section describing all of the closed pull requests this week using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (title, body). If you do not know something, say you do not know instead of making something up. 
#   Follow this structure: 
#   Use '## Closed PRs' as the main header. 
#   Use '### PR: ' + (title of pull request) for each subheading. 
#   Use a bullet point with 2-3 sentences giving a description of each closed PR. If there are more than 10 PRs, cluster some PRs together so there are at most 10 bullet points.
#   Show the output with markdown tags in a code block. Do not just give regular output."""

#   data = repo['closed_pull_requests']
  
#   return generate_summary(instructions, data).strip()


# # 8 - COMMITS: Statistics
# def commits_statistics(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
#   Create the newsletter section describing all of the commits made this week using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (commit message). If you do not know something, say you do not know instead of making something up. 
#   Follow this structure: 
#   Use '## Commits' as the main header. 
#   Use '### Number of Commits' for the subheading. 
#   A bullet point with 2-3 sentences giving a description of the number of commits this week. 
#   Use '### Commits Summary' for the subheading. 
#   Multiple bullet points with 2-3 sentences each clumping commit messages together and describing what the commits are about based on their messages. You should have no more than 10 bullet points for this section.
#   Show the output with markdown tags in a code block. Do not just give regular output."""

#   data = {
#     "num_commits": repo['num_commits'],
#     "commits": repo['commits']
#   }

#   return generate_summary(instructions, data).strip()


# # 9 - CONTRIBUTORS: Statistics
# def contributors_statistics(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
#   Create the newsletter section describing all of the new contributors this week, total contributors this week, and active contributors in the project using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (numbers of contributors). If you do not know something, say you do not know instead of making something up. 
#   Follow this structure: 
#   Use '## Contributors' as the main header. 
#   Use '### New Contributors' for the subheading. 
#   A bullet point with 2-3 sentences giving a description of the number of new contributors this week. 
#   A bullet point listing some of the new contributors. This should only be one bullet point in total, and you do not need to name all new contributors.
#   Use '### Weekly Contributors' for the subheading. 
#   A bullet point with 2-3 sentences giving a description of the number of total contributors this week. 
#   A bullet point listing some of the contributors. This should only be one bullet point in total, and you do not need to name all contributors.
#   Use '### Active Contributors' for the subheading. A bullet point with 2-3 sentences giving a description of the number of active contributors in the project. 
#   A bullet point listing some of the active contributors. This should only be one bullet point in total, and you do not need to name all contributors.
#   Show the output with markdown tags in a code block. Do not just give regular output."""

#   data = {
#     "new_contributors": repo['new_contributors'],
#     "contributed_this_week": repo['contributed_this_week'],
#     "active_contributors": repo['active_contributors']
#   }

#   return generate_summary(instructions, data).strip()


def test(repo):
  instructions = """Just say something
  nice about me please"""

  data = "Perhaps about how I look"

  return generate_summary(instructions, data).strip()




if __name__ == '__main__':

  # folders to get data and output data
  github_directory = 'github_data'
  newsletter_directory = 'newsletter_data'
  
  # creates the output directory if it doesn't exist
  if not os.path.exists(newsletter_directory):
    os.makedirs(newsletter_directory)
    
  # generate a newsletter for each file in the github_data folder
  for filename in os.listdir(github_directory):
    if filename.startswith('github') and filename.endswith('.json'):

      # saves the json contents into 'repo'
      filepath = os.path.join(github_directory, filename)
      with open(filepath, 'r') as file:
        repo = json.load(file)

        # creates name of file to output data (ex. newsletter_tensorflow_tensorflow)
        project_name = filename.split('github_')[1].rsplit('.json')[0]
        newsletter_filename = os.path.join(newsletter_directory, f"newsletter_{project_name}.txt")
        
        # creates the capitalized project name for the title in the newsletter
        name = project_name.split('_')[-1]
        capitalized_name = name[0].upper() + name[1:]

        try:
          with open(newsletter_filename, "w") as outfile:

            # 0: Title
            title = f"# Report for {capitalized_name}\n\n"
            outfile.write(title)

            # 0.1: Description underneath the title
            caption = ("Thank you for subscribing to our weekly newsletter! Each week, we " +
                       "deliver a comprehensive summary of your GitHub project's latest activity " +
                       "right to your inbox, including an overview of your project's issues, " +
                       "pull requests, contributors, and commit activity.\n\n")
            outfile.write(caption)

            outfile.write("***\n\n")



            # 1: Issues
            outfile.write("# I. Issues\n")

            # 1.1: Open Issues
            outfile.write("## 1.1 Open Issues\n")

            # 1.1.1 Open Issues This Week
            outfile.write(f"**Open Issues This Week:** {repo.get('num_weekly_open_issues', None)}\n\n")

            # 1.1.2 Issues
            outfile.write("**Issues:**\n\n")
            # TODO get chatgpt to write a summary of the issues


            # 1.2: Closed Issues
            outfile.write("## 1.2 Closed Issues\n")

            # 1.2.1 Closed Issues This Week
            outfile.write(f"**Closed Issues This Week:** {repo.get('num_weekly_closed_issues', None)}\n\n")

            # 1.2.2 Average Time to Close Issues This Week
            outfile.write(f"**Average Issue Close Time (This Week):** {repo.get('average_issue_close_time_weekly', None)}\n\n")

            # 1.2.3 Average Time to Close Issues All Time
            outfile.write(f"**Average Issue Close Time (All Time):** {repo.get('average_issue_close_time', None)}\n\n")

            # 1.2.4 Issues
            outfile.write("**Issues:**\n\n")
            # TODO get chatgpt to write a summary of the issues

            outfile.write("***\n\n")



            # 2: Pull Requests
            outfile.write("# II. Pull Requests\n")

            # 2.1: Open Pull Requests
            outfile.write("## 2.1 Open Pull Requests\n")

            # 2.1.1 Open Pull Requests This Week
            outfile.write(f"**Open Pull Requests This Week:** {repo.get('num_open_prs', None)}\n\n")

            # 2.1.2 Pull Requests
            outfile.write("**Pull Requests:**\n\n")
            # TODO get chatgpt to write a summary of the pull requests


            # 2.2: Closed Pull Requests
            outfile.write("## 2.2 Closed Pull Requests\n")

            # 2.2.1 Closed Pull Requests This Week
            outfile.write(f"**Closed Pull Requests This Week:** {repo.get('num_closed_prs', None)}\n\n")

            # 2.2.2 Pull Requests
            outfile.write("**Pull Requests:**\n\n")
            # TODO get chatgpt to write a summary of the pull requests







            

          print(f"Successfully added {project_name} to {newsletter_filename}")
        
        except Exception as e:
          print(f"Error writing {project_name} to {newsletter_filename}")
          print(f"Error code: {e}")