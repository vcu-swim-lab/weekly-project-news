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
# llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key = API_KEY)
chain = PROMPT | llm


# Generates the summary using ChatGPT given any context and question (prompt template above)
def generate_summary(instructions, data):
    response = chain.invoke({"instructions": instructions, "data": data})

    input_tokens = response.runnables[0].input_tokens
    output_tokens = response.runnables[1].output_tokens
    print(f"Input Tokens: {input_tokens}")
    print(f"Output Tokens: {output_tokens}")

    return response.content


# 1 - ISSUES: Stastics
def issues_statistics(repo):
  instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
  Create the newsletter section describing all of the total open issues, issues opened this week, and issues closed this week using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (numbers). If you do not know something, say you do not know instead of making something up. 
  Follow this structure: 
  Use '## Statistics' as the main header. 
  Use '### Total Open Issues' for the subheading.
  A bullet point with 2-3 sentences giving a description of the total open issues this week. 
  Use '### Issues Opened This Week' for the subheading.
  A bullet point with 2-3 sentences giving a description of the issues opened this week.
  Use '### Issues Closed This Week' for the subheading. 
  A bullet point with 2-3 sentences giving a description of the issues closed this week. 
  Use '### All Open Issues' for the subheading.
  A bullet point with 2-3 sentences giving a description of each open issue based on comments, body, and issue title. If there are more than 10 issues, cluster some bullet points together so there are at most 10 bullet points.
  Show the output with markdown tags in a code block. Do not just give regular output."""

  data = {
    "num_all_open_issues": repo['num_all_open_issues'],
    "num_weekly_open_issues": repo['num_weekly_open_issues'],
    "num_weekly_closed_issues": repo['num_weekly_closed_issues'],
    "open_issues": repo['open_issues']
  }

  return generate_summary(instructions, data).strip()


# 2 - ISSUES: Active Open Issues in the Past Week
def issues_statistics(repo):
  instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
  Create the newsletter section describing all active issues opened this week (indicated by number of comments) using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (title, number of comments). If you do not know something, say you do not know instead of making something up. 
  Follow this structure: 
  Use '## Active Open Issues in the Past Week' as the main header. 
  Use '### Issue: ' + (title of issue) for each subheading. 
  A bullet point giving a link to the active issue, then a bullet point with 2-3 sentences giving a description of each active issue. If there are more than 10 issues, cluster some issues together so there are at most 10 bullet points.
  Show the output with markdown tags in a code block. Do not just give regular output."""

  data = repo['issues_by_number_of_comments']

  return generate_summary(instructions, data).strip()


# 3 - ISSUES: Quiet Open Issues Currently
def issues_statistics(repo):
  instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
  Create the newsletter section describing all issues that have gone quiet (indicated by time still opened) using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (title, time open). If you do not know something, say you do not know instead of making something up. 
  Follow this structure: 
  Use '## Quiet Open Issues Currently' as the main header. 
  Use '### Issue: ' + (title of issue) for each subheading. 
  A bullet point giving a link to the open issue, then a bullet point with 2-3 sentences giving a description of each open issue. If there are more than 10 issues, only list the top 10 oldest open issues.
  Show the output with markdown tags in a code block. Do not just give regular output."""

  data = repo['issues_by_open_date']
  
  return generate_summary(instructions, data).strip()


# 4 - ISSUES: Closed Issues
def issues_statistics(repo):
  instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
  Create the newsletter section describing all issues that have been closed this week using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (title, body, any comments). If you do not know something, say you do not know instead of making something up. 
  Follow this structure: 
  Use '## Closed Issues' as the main header. 
  Use '### Issue: ' + (title of issue) for each subheading. 
  A bullet point giving a link to the closed issue, then a bullet point with 2-3 sentences giving a description of each closed issue. If there are more than 10 issues, only list 10 issues.
  Show the output with markdown tags in a code block. Do not just give regular output."""

  data = repo['issues_closed']

  return generate_summary(instructions, data).strip()











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

        # get the project name (ex. tensorflow_tensorflow)
        project_name = filename.split('github_')[1].rsplit('.json')[0]

        # get the file name in the output folder (ex. newsletter_tensorflow_tensorflow)
        newsletter_filename = os.path.join(newsletter_directory, f"newsletter_{project_name}.txt")

        try:
          with open(newsletter_filename, "w") as outfile:

            # TODO: project_name is still something like monicahq_monica
            title = f"# Report for {project_name}\n\n"
            outfile.write(title)

            # caption underneath the title
            caption = ("Thank you for subscribing to our weekly newsletter! Each week, we " +
                       "deliver a comprehensive summary of your GitHub project’s latest activity " +
                       "right to your inbox, including an overview of your project’s issues, " +
                       "pull requests, contributors, and commit activity.\n\n")
            outfile.write(caption)

            # 1 - ISSUES: Statistics
            # issues_statistics = issues_statistics(repo)
            # outfile.write(issues_statistics)



          print(f"Successfully added {project_name} to {newsletter_filename}")
        except Exception as e:
          print(f"Error writing {project_name} to {newsletter_filename}")
          print(f"Error code: {e}")


# def test(repo):
#   instructions = """You are a GitHub project maintainer writing a newsletter that gives a summary of your project's issues, pull requests, commits, contributors, and statistics. 
# Create the newsletter section describing all of the new contributors this week, total contributors this week, and active contributors in the project using the JSON data below. The output should be informational, descriptive, and only based on the JSON data given (numbers of contributors). If you do not know something, say you do not know instead of making something up. 

# Follow this structure: 

# Use '## Contributors' as the main header. 
# Use '### New Contributors’ for the subheading. 
# A bullet point with 2-3 sentences giving a description of the number of new contributors this week. 
# A bullet point listing some of the new contributors. This should only be one bullet point in total, and you do not need to name all new contributors.
# Use '### Weekly Contributors’ for the subheading. 
# A bullet point with 2-3 sentences giving a description of the number of total contributors this week. 
# A bullet point listing some of the contributors. This should only be one bullet point in total, and you do not need to name all contributors.
# Use '### Active Contributors’ for the subheading. 
# A bullet point with 2-3 sentences giving a description of the number of active contributors in the project. 
# A bullet point listing some of the active contributors. This should only be one bullet point in total, and you do not need to name all contributors.

# Show the output with markdown tags in a code block. Do not just give regular output.
# """

#   data = {
#     "new_contributors": repo['new_contributors'],
#     "contributed_this_week": repo['contributed_this_week'],
#     "active_contributors": repo['active_contributors']
#   }

#   return generate_summary(instructions, data).strip()