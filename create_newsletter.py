import json
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate
import re

load_dotenv()  

API_KEY = os.environ.get("OPENAI_KEY")

# https://stackoverflow.com/questions/77316112/langchain-how-do-input-variables-work-in-particular-how-is-context-replaced
prompt_template = "Data: {data}\nInstructions: {instructions}\n"
PROMPT = PromptTemplate(template=prompt_template, input_variables=["data", "instructions"])
llm=ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key = API_KEY)
chain = PROMPT | llm

# param1: "a closed issue", param2-3: "issue", param4: "only one detailed sentence"
def individual_instructions(param1, param2, param3, param4):
  return f"Above is JSON data describing {param1} from a GitHub project. Give {param4} describing what this {param2} is about, starting with 'This {param3}'"

# param1-4: "issues", param5: true if should include in instructions
def general_instructions(param1, param2, param3, param4, param5, param6):
  instructions = f"Generate a bulleted list in markdown where each bullet point starts with a concise topic covered by multiple {param1} in bold text, followed by a colon, followed by a one paragraph summary that must contain {param6} sentences describing the topic's {param2}. This topic, colon, and paragraph summary must all be on the same line on the same bullet point. "
  if param5:
    instructions += f"After each bullet point, there should be indented bullet points giving just the URLs of the {param3} that the topic covers, no other text. "
  instructions += f"You must clump {param4} with similar topics together, so there are fewer bullet points. Show the output in markdown in a code block.\n"
  return instructions

# Generates the summary using ChatGPT given any context and question (prompt template above)
def generate_summary(data, instructions):
    response = chain.invoke({"data": instructions, "instructions": data})
    return response.content



# 1 - Open Issues
def open_issues(repo):

  all_open_issues = ""
  issue_instructions = individual_instructions("an open issue", "issue", "issue", "only one detailed sentence")
  overall_instructions = general_instructions("issues", "issues", "issues", "issues", True, 3)

  if repo['open_issues'] == [] :
    return "As of our latest update, there are no open issues for the project this week. This indicates that all reported bugs, feature requests, or other concerns have been addressed or are not currently being actively pursued.\n\n"

  # Step 1: get summaries for each open issue first from the llm
  for open_issue in repo['open_issues']:
    data = open_issue
   
    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])
      for comment in data.get('comments', []):
        comment['body'] = re.sub(r'<img[^>]*>|\r\n', '', comment['body'])
    
    # issue_summary = data
    issue_summary = generate_summary(data, issue_instructions)
    issue_url = f"URL: {open_issue.get('url')}"
    all_open_issues += f"{issue_summary}\n{issue_url}\n\n"

  print("\n", all_open_issues, "\n\n\n")
  
  # Step 2: get markdown output for all open issues 
  overall_summary = generate_summary(all_open_issues, overall_instructions)
  if overall_summary.startswith("```") and overall_summary.endswith("```"):
    overall_summary = overall_summary[3:-3]
  if overall_summary.startswith("markdown"):
    overall_summary = overall_summary[len("markdown"):].lstrip()
  return overall_summary + "\n"


# 2 - Open Issues (Active)
def active_issues(repo):

  markdown = "We consider active issues to be issues that have generated much discussion in the issue's comments. \n\n"
  issue_instructions = individual_instructions("an open issue", "issue", "issue", "two detailed sentences")
  issues = repo['issues_by_number_of_comments']
  size = min(len(issues), 5)

  for i in range(size):
    data = issues[i]
    issue_title = data.get('title')
    issue_summary = generate_summary(data, issue_instructions)

    # Start each issue on a numbered list
    markdown += f"{i + 1}. **{issue_title}**: {issue_summary}\n"
    markdown += f"   - Open for {data.get('time_open')}\n"
    markdown += f"   - {data.get('url')}\n\n"

  if (size == 0):
    markdown += "Since there were no open issues for the project this week, no active issues could be listed.\n\n"
  elif (size < 5):
    markdown += f"Since there were fewer than 5 open issues, all of the open issues have been listed above.\n\n"

  print("\n", markdown, "\n\n\n")
  return markdown



# 3 - Open Issues (Quiet)
def quiet_issues(repo):

  markdown = "We consider quiet issues to be issues that have been opened in this project for the longest time. The team should work together to get these issues resolved and closed as soon as possible. \n\n"
  issue_instructions = individual_instructions("an open issue", "issue", "issue", "two detailed sentences")
  issues = repo['issues_by_open_date']
  size = min(len(issues), 5)

  for i in range(size):
    data = issues[i]
    issue_title = data.get('title')
    issue_summary = generate_summary(data, issue_instructions)

    # Start each issue on a numbered list
    markdown += f"{i + 1}. **{issue_title}**: {issue_summary}\n"
    markdown += f"   - Open for {data.get('time_open')}\n"
    markdown += f"   - {data.get('url')}\n\n"

  if (size == 0):
    markdown += "Since there were no open issues for the project this week, no active issues could be listed.\n\n"
  elif (size < 5):
    markdown += f"Since there were fewer than 5 open issues, all of the open issues have been listed above.\n\n"

  print("\n", markdown, "\n\n\n")
  return markdown



# 4 - Closed Issues
def closed_issues(repo):

  all_closed_issues = ""
  issue_instructions = individual_instructions("a closed issue", "issue", "issue", "only one detailed sentence")
  overall_instructions = general_instructions("issues", "issues", "issues", "issues", True, 3)

  if repo['closed_issues'] == []:
    return "As of our latest update, there are no closed issues for the project this week.\n\n"

  # Step 1: get summaries for each closed issue first from the llm
  for closed_issue in repo['closed_issues']:
    data = closed_issue
   
    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])
      for comment in data.get('comments', []):
        comment['body'] = re.sub(r'<img[^>]*>|\r\n', '', comment['body'])
    
    # issue_summary = data
    issue_summary = generate_summary(data, issue_instructions)
    issue_url = f"URL: {closed_issue.get('url')}"
    all_closed_issues += f"{issue_summary}\n{issue_url}\n\n"

  print("\n", all_closed_issues, "\n\n\n")
  
  # Step 2: get markdown output for all closed issues 
  overall_summary = generate_summary(all_closed_issues, overall_instructions)
  if overall_summary.startswith("```") and overall_summary.endswith("```"):
    overall_summary = overall_summary[3:-3]
  if overall_summary.startswith("markdown"):
    overall_summary = overall_summary[len("markdown"):].lstrip()
  return overall_summary + "\n"


# 5 - Open Pull Requests
def open_pull_requests(repo):

  all_pull_requests = ""
  pull_request_instructions = individual_instructions("an open pull request", "pull request", "pull request", "only one detailed sentence")
  overall_instructions = general_instructions("pull requests", "pull requests", "pull requests", "pull requests", True, 3)

  if repo['open_pull_requests'] == []:
    return "As of our latest update, there are no open pull requests for the project this week.\n\n"

  # Step 1: get summaries for each open pull request first from the llm
  for pull_request in repo['open_pull_requests']:
    data = pull_request
   
    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])

    # pull_request_summary = data
    pull_request_summary = generate_summary(data, pull_request_instructions)
    pull_request_url = f"URL: {pull_request.get('url')}"
    all_pull_requests += f"{pull_request_summary}\n{pull_request_url}\n\n"

  print("\n", all_pull_requests, "\n\n\n")

  # Step 2: get markdown output for all open pull requests 
  overall_summary = generate_summary(all_pull_requests, overall_instructions)
  if overall_summary.startswith("```") and overall_summary.endswith("```"):
    overall_summary = overall_summary[3:-3]
  if overall_summary.startswith("markdown"):
    overall_summary = overall_summary[len("markdown"):].lstrip()
  return overall_summary + "\n"


# 6 - Closed Pull Requests
def closed_pull_requests(repo):

  all_pull_requests = ""
  pull_request_instructions = individual_instructions("a closed pull request", "pull request", "pull request", "only one detailed sentence")
  overall_instructions = general_instructions("pull requests", "pull requests", "pull requests", "pull requests", True, 3)

  if repo['closed_pull_requests'] == []:
    return "As of our latest update, there are no closed pull requests for the project this week.\n\n"

  # Step 1: get summaries for each closed pull request first from the llm
  for pull_request in repo['closed_pull_requests']:
    data = pull_request
   
    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])

    # pull_request_summary = data
    pull_request_summary = generate_summary(data, pull_request_instructions)
    pull_request_url = f"URL: {pull_request.get('url')}"
    all_pull_requests += f"{pull_request_summary}\n{pull_request_url}\n\n"

  print("\n", all_pull_requests, "\n\n\n")

  # Step 2: get markdown output for all closed pull requests 
  overall_summary = generate_summary(all_pull_requests, overall_instructions)
  if overall_summary.startswith("```") and overall_summary.endswith("```"):
    overall_summary = overall_summary[3:-3]
  if overall_summary.startswith("markdown"):
    overall_summary = overall_summary[len("markdown"):].lstrip()
  return overall_summary + "\n"


# 7 - Commits
def commits(repo):

  all_commits = ""
  commit_instructions = individual_instructions("a commit", "commit", "commit", "only one detailed sentence")
  overall_instructions = general_instructions("commits", "commits", "commits", "commits", False, 2)

  if repo['commits'] == []:
    return "As of our latest update, there are no commits for the project this week.\n\n"

  # Step 1: get summaries for each commit first from the llm
  for commit in repo['commits']:
    data = commit
   
    if (data['message']):
      data['message'] = re.sub(r'<img[^>]*>|\r\n', '', data['message'])

    # commit_summary = data
    commit_summary = generate_summary(data, commit_instructions)
    all_commits += f"{commit_summary}\n\n"

  print("\n", all_commits, "\n\n\n")

  # Step 2: get markdown output for all commits
  overall_summary = generate_summary(all_commits, overall_instructions)
  if overall_summary.startswith("```") and overall_summary.endswith("```"):
    overall_summary = overall_summary[3:-3]
  if overall_summary.startswith("markdown"):
    overall_summary = overall_summary[len("markdown"):].lstrip()
  return overall_summary + "\n"


# 8 - Active Contributors
def active_contributors(repo):

  overall_summary = "We consider an active contributor in this project to be any contributor who has made at least 1 commit, opened at least 1 issue, or created at least 1 pull request in the past week. \n\n"
 
  if repo['active_contributors'] == []:
    overall_summary += "As of our latest update, there are no active contributors for the project this week.\n\n"
    return overall_summary

  overall_summary += "Contributor | Commits | Pull Requests | Issues \n"
  overall_summary += "---|---|---|---\n"

  # Step 1: filter out non-contributor entries and aggregate data
  contributors = []
  for contributor in repo['active_contributors']:
    if 'author' in contributor:  # Skip entries without 'author'
      total_activity = contributor['commits'] + contributor['pull_requests'] + contributor['issues']
      contributor['total_activity'] = total_activity
      contributors.append(contributor)

  # Step 2: sort contributors by total_activity in descending order
  sorted_contributors = sorted(contributors, key=lambda x: x['total_activity'], reverse=True)

  # Step 3: generate markdown output for all active contributors
  for contributor in sorted_contributors:
    overall_summary += contributor['author'] + " | "
    overall_summary += f"{contributor['commits']}" + " | "
    overall_summary += f"{contributor['pull_requests']}" + " | "
    overall_summary += f"{contributor['issues']}" + " | \n"
    
  return overall_summary











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
            title = f"# Weekly GitHub Report for {capitalized_name}\n\n"
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
            outfile.write("**Summarized Issues:**\n\n")
            # result = open_issues(repo)
            # outfile.write(result)


            # 1.2 Top 5 Active Issues
            outfile.write("## 1.2 Top 5 Active Issues:\n")
            # result = active_issues(repo)
            # outfile.write(result)


            # 1.3 Top 5 Quiet Issues
            outfile.write("## 1.3 Top 5 Quiet Issues:\n")
            # result = quiet_issues(repo)
            # outfile.write(result)


            # 1.4: Closed Issues
            outfile.write("## 1.4 Closed Issues\n")

            # 1.4.1 Closed Issues This Week
            outfile.write(f"**Closed Issues This Week:** {repo.get('num_weekly_closed_issues', None)}\n\n")

            # 1.4.2 Average Time to Close Issues This Week
            outfile.write(f"**Average Issue Close Time (This Week):** {repo.get('average_issue_close_time_weekly', None)}\n\n")

            # 1.4.3 Average Time to Close Issues All Time
            outfile.write(f"**Average Issue Close Time (All Time):** {repo.get('average_issue_close_time', None)}\n\n")

            # 1.4.4 Issues
            outfile.write("**Summarized Issues:**\n\n")
            # result = closed_issues(repo)
            # outfile.write(result)

            outfile.write("***\n\n")



            # 2: Pull Requests
            outfile.write("# II. Pull Requests\n")

            # 2.1: Open Pull Requests
            outfile.write("## 2.1 Open Pull Requests\n")

            # 2.1.1 Open Pull Requests This Week
            outfile.write(f"**Open Pull Requests This Week:** {repo.get('num_open_prs', None)}\n\n")

            # 2.1.2 Pull Requests
            outfile.write("**Pull Requests:**\n\n")
            # result = open_pull_requests(repo)
            # outfile.write(result)


            # 2.2: Closed Pull Requests
            outfile.write("## 2.2 Closed Pull Requests\n")

            # 2.2.1 Closed Pull Requests This Week
            outfile.write(f"**Closed Pull Requests This Week:** {repo.get('num_closed_prs', None)}\n\n")

            # 2.2.2 Pull Requests
            outfile.write("**Summarized Pull Requests:**\n\n")
            # result = closed_pull_requests(repo)
            # outfile.write(result)

            outfile.write("***\n\n")



            # 3: Commits
            outfile.write("# III. Commits\n")

            # 3.1: Open Commits
            outfile.write("## 3.1 Commits\n")

            # 3.1.1 Open Commits This Week
            outfile.write(f"**Commits This Week:** {repo.get('num_commits', None)}\n\n")

            # 3.1.2 Commits
            outfile.write("**Summarized Commits:**\n\n")
            # result = commits(repo)
            # outfile.write(result)

            outfile.write("***\n\n")



            # 4: Contributors
            outfile.write("# IV. Contributors\n")

            # 4.1: Contributors
            outfile.write("## 4.1 Contributors\n")

            # 4.1.1 New Contributors
            outfile.write(f"**New Contributors:** {repo.get('new_contributors')[-1].get('number_of_new_contributors')}\n\n")

            # 4.1.2 New Contributors
            outfile.write(f"**Total Contributors This Week:** {repo.get('contributed_this_week')[-1].get('number_of_weekly_contributors')}\n\n")

            # 4.1.4 Active Contributors
            outfile.write("**Active Contributors:**\n\n")
            result = active_contributors(repo)
            outfile.write(result)

            outfile.write("***\n\n")


          print(f"Successfully added {project_name} to {newsletter_filename}")
        
        except Exception as e:
          print(f"Error writing {project_name} to {newsletter_filename}")
          print(f"Error code: {e}")
