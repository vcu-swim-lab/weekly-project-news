import json
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate
import re
import time
import random
from openai import RateLimitError
from sort_data import *
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from collections import deque
import openai

load_dotenv()  

API_KEY = os.environ.get("OPENAI_KEY")

# https://stackoverflow.com/questions/77316112/langchain-how-do-input-variables-work-in-particular-how-is-context-replaced
prompt_template = "Data: {data}\nInstructions: {instructions}\n"
PROMPT = PromptTemplate(template=prompt_template, input_variables=["data", "instructions"])
llm=ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key = API_KEY)
chain = PROMPT | llm

# param1: "a closed issue", param2-3: "issue", param4: "only one detailed sentence"
def individual_instructions(param1, param2, param3, param4):
  return f"Above is JSON data describing {param1} from a GitHub project. Give {param4} describing what this {param2} is about, starting with 'This {param3}'. "

# param1-4: "issues", param5: true if should include in instructions
def general_instructions(param1, param2, param3, param4, param5, param6):
  instructions = f"Generate a bulleted list in markdown where each bullet point starts with a concise topic covered by multiple {param1} in bold text, followed by a colon, followed by a one paragraph summary that must contain {param6} sentences describing the topic's {param2}. This topic, colon, and paragraph summary must all be on the same line on the same bullet point. "
  if param5:
    instructions += f"After each bullet point, there should be indented bullet points giving just the URLs of the {param3} that the topic covers, no other text. Each URL must start with 'github.com', so no https or anything. "
  instructions += f"You must clump {param4} with similar topics together, so there are fewer bullet points. Show the output in markdown in a code block.\n"
  return instructions


def discussion_instructions():
  return """First, write a one paragraph summary capturing the trajectory of a GitHub conversation. Do not include specific topics, claims, or arguments from the conversation. Be concise and objective with the sentences describing the trajectory, including usernames, sentiments, tones, and triggers of tension. For example, 'username1 expresses frustration that username2's solution did not work'. Start your answer with 'This GitHub conversation'"
After that paragraph, on a different line, give only a single number to 2 decimal places on a 0 to 1 scale describing the possibility of occurring toxicity in future comments, where 0 to 0.3 should be very little toxicity, 0.3 to 0.6 should be a bit higher, and 0.6 to 1 should be alarming. Do not output anything else on this line.
Then, on a different line, give only a short comma-separated list of specific reasons in the summary for giving the number. For example, 'Rapid escalation, aggressive language'"""


total_tokens = 0
total_requests = 0
minute_start_time = datetime.now()

# Generates summary using gpt-4o given context and question (prompt_template above)
# Uses exponential backoff as a backoff timer
def generate_summary(data, instructions, max_retries=5, base_wait=1):
    global total_requests, total_tokens, minute_start_time

    for attempt in range(max_retries):
        try:
            current_time = datetime.now()

            # if over a minute, reset
            if (current_time - minute_start_time).total_seconds() >= 60:
                total_requests = 0
                total_tokens = 0
                minute_start_time = current_time
                print("\n--- New Minute: Counters Reset ---\n")

            # print('data:')
            # print(data)
            # print()
            response = chain.invoke({"data": instructions, "instructions": data})
            tokens_used = response.usage_metadata['total_tokens']
            total_tokens += tokens_used
            total_requests += 1

            time_elapsed = (current_time - minute_start_time).total_seconds()

            print(f"\n--- API Call Complete ---")
            print(f"Tokens used in this request:    {tokens_used} tokens")
            print(f"Total tokens used this minute:  {total_tokens} tokens")
            print(f"Total requests made:            {total_requests} requests")
            print(f"Time elapsed in current minute: {time_elapsed:.2f} seconds")
            print("------------------------\n")

            return response.content
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = (2 ** attempt) * base_wait + random.uniform(0, 1)
            print(f"Rate limit reached. Waiting for {wait_time:.2f} seconds before retrying...")
            time.sleep(wait_time)



# 1 - Open Issues
def open_issues(repo):
  if repo['open_issues'] == [] :
    return "As of our latest update, there are no open issues for the project this week.\n\n"

  all_open_issues = ""
  issue_instructions = individual_instructions("an open issue", "issue", "issue", "only one detailed sentence")
  overall_instructions = general_instructions("issues", "issues", "issues", "issues", True, 3)

  # Step 1: get summaries for each open issue first from the llm
  for open_issue in repo['open_issues']:
    data = open_issue
   
    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])
      for comment in data.get('comments', []):
        comment['body'] = re.sub(r'<img[^>]*>|\r\n', '', comment['body'])
    
    # issue_summary = data
    issue_summary = generate_summary(data, issue_instructions, max_retries=5, base_wait=1)
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
  if repo['issues_by_number_of_comments'] == []:
    markdown += "As of our latest update, there are no active issues with ongoing comments this week. \n\n"
    return markdown

  issue_instructions = individual_instructions("an open issue", "issue", "issue", "two detailed sentences")
  issue_instructions += "Do not mention the URL in the summary. After each bullet point, you must give only one indented bullet point in markdown (starting with three spaces, then '-') summarizing the interaction in the comments, which can be multiple concise sentences. You must only give ONE bullet point per 10 comments. If there are fewer than 10 comments, only give 1 bullet point. Do not mention specific usernames."
  issues = repo['issues_by_number_of_comments']
  size = min(len(issues), 5)

  # We are only summarizing the top 5 open issues (active)
  for i in range(size):
    data = issues[i]
    issue_title = data.get('title')
    issue_summary = generate_summary(data, issue_instructions, max_retries=5, base_wait=1)
    issue_url = data.get('url')

    # Make the issue title a clickable link
    markdown += f"{i + 1}. [**{issue_title}**]({issue_url}): {issue_summary}\n"
    markdown += f"   - Number of comments: {data.get('number_of_comments')}\n\n"

  if (size < 5):
    markdown += f"Since there were fewer than 5 open issues, all of the open issues have been listed above.\n\n"

  print("\n", markdown, "\n\n\n")
  return markdown



# 3 - Open Issues (Quiet)
def quiet_issues(repo):
  markdown = "We consider quiet issues to be issues that have been opened in this project for the longest time. The team should work together to get these issues resolved and closed as soon as possible. \n\n"
  if repo['issues_by_open_date'] == []:
    markdown += "As of our latest update, there are no open issues for the project this week. \n\n"
    return markdown

  issue_instructions = individual_instructions("an open issue", "issue", "issue", "two detailed sentences")
  issue_instructions += "Do not mention the URL in the summary."
  issues = repo['issues_by_open_date']
  size = min(len(issues), 5)

  # We are only summarizing the top 5 open issues (quiet)
  for i in range(size):
    data = issues[i]
    issue_title = data.get('title')
    issue_summary = generate_summary(data, issue_instructions, max_retries=5, base_wait=1)
    issue_url = data.get('url')

    # Make the issue title a clickable link
    markdown += f"{i + 1}. [**{issue_title}**]({issue_url}): {issue_summary}\n"
    markdown += f"   - Open for {data.get('time_open')}\n\n"

  if (size < 5):
    markdown += f"Since there were fewer than 5 open issues, all of the open issues have been listed above.\n\n"

  print("\n", markdown, "\n\n\n")
  return markdown



# 4 - Closed Issues
def closed_issues(repo):
  if repo['closed_issues'] == []:
    return "As of our latest update, there are no closed issues for the project this week.\n\n"

  all_closed_issues = ""
  issue_instructions = individual_instructions("a closed issue", "issue", "issue", "only one detailed sentence")
  overall_instructions = general_instructions("issues", "issues", "issues", "issues", True, 3)

  # Step 1: get summaries for each closed issue first from the llm
  for closed_issue in repo['closed_issues']:
    data = closed_issue
   
    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])
      for comment in data.get('comments', []):
        comment['body'] = re.sub(r'<img[^>]*>|\r\n', '', comment['body'])
    
    # issue_summary = data
    issue_summary = generate_summary(data, issue_instructions, max_retries=5, base_wait=1)
    issue_url = f"URL: {closed_issue.get('url')}"
    all_closed_issues += f"{issue_summary}\n{issue_url}\n\n"

  print("\n", all_closed_issues, "\n\n\n")
  
  # Step 2: get markdown output for all closed issues 
  overall_summary = generate_summary(all_closed_issues, overall_instructions, max_retries=5, base_wait=1)
  if overall_summary.startswith("```") and overall_summary.endswith("```"):
    overall_summary = overall_summary[3:-3]
  if overall_summary.startswith("markdown"):
    overall_summary = overall_summary[len("markdown"):].lstrip()
  return overall_summary + "\n\n"



# 5 - Issue Discussion Insights
def issue_discussion_insights(repo):
  markdown = "This section will analyze the tone and sentiment of discussions within this project's open issues within the past week to identify potentially heated exchanges and to maintain a constructive project environment. \n\n"
  if repo['active_issues'] == []:
    markdown += "As of our last update, there are no open issues with discussions going on within the past week. \n\n"
    return markdown
  
  issue_count = 0

  for active_issue in repo['active_issues']:
    instructions = discussion_instructions()
  
    generated_summary = generate_summary(active_issue, instructions, max_retries=5, base_wait=1)

    parts = generated_summary.rsplit('\n\n', 2)
    summary = parts[0].strip()
    score = float(parts[1])
    reason = parts[2].strip()

    if score > 0.5:
      issue_count += 1
      
      markdown += f"{issue_count}. [**{active_issue['title']}**]({active_issue['url']})\n"
      markdown += f"   - Toxicity Score: {score:.2f} ({reason})\n"
      markdown += f"   - {summary}\n\n"
    
  if issue_count == 0:
    markdown += "Based on our analysis, there are no instances of toxic discussions in the project's open issues from the past week. \n\n"
    
  return markdown
  


# 6 - Open Pull Requests
def open_pull_requests(repo):
  if repo['open_pull_requests'] == []:
    return "As of our latest update, there are no open pull requests for the project this week.\n\n"

  all_pull_requests = ""
  pull_request_instructions = individual_instructions("an open pull request", "pull request", "pull request", "only one detailed sentence")
  overall_instructions = general_instructions("pull requests", "pull requests", "pull requests", "pull requests", True, 3)

  # Step 1: get summaries for each open pull request first from the llm
  for pull_request in repo['open_pull_requests']:
    data = pull_request
   
    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])

    # pull_request_summary = data
    pull_request_summary = generate_summary(data, pull_request_instructions, max_retries=5, base_wait=1)
    pull_request_url = f"URL: {pull_request.get('url')}"
    all_pull_requests += f"{pull_request_summary}\n{pull_request_url}\n\n"

  print("\n", all_pull_requests, "\n\n\n")

  # Step 2: get markdown output for all open pull requests 
  overall_summary = generate_summary(all_pull_requests, overall_instructions, max_retries=5, base_wait=1)
  if overall_summary.startswith("```") and overall_summary.endswith("```"):
    overall_summary = overall_summary[3:-3]
  if overall_summary.startswith("markdown"):
    overall_summary = overall_summary[len("markdown"):].lstrip()
  return overall_summary + "\n"


# 7 - Closed Pull Requests
def closed_pull_requests(repo):
  if repo['closed_pull_requests'] == []:
    return "As of our latest update, there are no closed pull requests for the project this week.\n\n"

  all_pull_requests = ""
  pull_request_instructions = individual_instructions("a closed pull request", "pull request", "pull request", "only one detailed sentence")
  overall_instructions = general_instructions("pull requests", "pull requests", "pull requests", "pull requests", True, 3)

  # Step 1: get summaries for each closed pull request first from the llm
  for pull_request in repo['closed_pull_requests']:
    data = pull_request
   
    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])

    # pull_request_summary = data
    pull_request_summary = generate_summary(data, pull_request_instructions, max_retries=5, base_wait=1)
    pull_request_url = f"URL: {pull_request.get('url')}"
    all_pull_requests += f"{pull_request_summary}\n{pull_request_url}\n\n"

  print("\n", all_pull_requests, "\n\n\n")

  # Step 2: get markdown output for all closed pull requests 
  overall_summary = generate_summary(all_pull_requests, overall_instructions, max_retries=5, base_wait=1)
  if overall_summary.startswith("```") and overall_summary.endswith("```"):
    overall_summary = overall_summary[3:-3]
  if overall_summary.startswith("markdown"):
    overall_summary = overall_summary[len("markdown"):].lstrip()
  return overall_summary + "\n\n"



# 8 - Pull Request Discussion Insights
def pull_request_discussion_insights(repo):
  markdown = "This section will analyze the tone and sentiment of discussions within this project's open pull requests within the past week to identify potentially heated exchanges and to maintain a constructive project environment. \n\n"
  if repo['active_pull_requests'] == []:
    markdown += "As of our last update, there are no open pull requests with discussions going on within the past week. \n\n"
    return markdown
  
  pull_request_count = 0

  for active_pull_request in repo['active_pull_requests']:
    instructions = discussion_instructions()
  
    generated_summary = generate_summary(active_pull_request, instructions, max_retries=5, base_wait=1)

    parts = generated_summary.rsplit('\n\n', 2)
    summary = parts[0].strip()
    print("Summary: ", summary)

    score = float(parts[1])
    print("Score: ", score)

    reason = parts[2].strip()
    print("Reason: ", reason)

    if score > 0.5:
      pull_request_count += 1
      
      markdown += f"{pull_request_count}. [**{active_pull_request['title']}**]({active_pull_request['url']})\n"
      markdown += f"   - Toxicity Score: {score:.2f} ({reason})\n"
      markdown += f"   - {summary}\n\n"
    
  if pull_request_count == 0:
    markdown += "Based on our analysis, there are no instances of toxic discussions in the project's open pull requests from the past week. \n\n"
    
  return markdown


# 9 - Commits
def commits(repo):
  if repo['commits'] == []:
    return "As of our latest update, there are no commits for the project this week.\n\n"

  all_commits = ""
  commit_instructions = individual_instructions("a commit", "commit", "commit", "only one detailed sentence")
  overall_instructions = general_instructions("commits", "commits", "commits", "commits", False, 2)

  # Step 1: get summaries for each commit first from the llm
  for commit in repo['commits']:
    data = commit
   
    if (data['message']):
      data['message'] = re.sub(r'<img[^>]*>|\r\n', '', data['message'])

    # commit_summary = data
    commit_summary = generate_summary(data, commit_instructions, max_retries=5, base_wait=1)
    all_commits += f"{commit_summary}\n\n"

  print("\n", all_commits, "\n\n\n")

  # Step 2: get markdown output for all commits
  overall_summary = generate_summary(all_commits, overall_instructions, max_retries=5, base_wait=1)
  if overall_summary.startswith("```") and overall_summary.endswith("```"):
    overall_summary = overall_summary[3:-3]
  if overall_summary.startswith("markdown"):
    overall_summary = overall_summary[len("markdown"):].lstrip()
  return overall_summary + "\n\n"


# 10 - Active Contributors
def active_contributors(repo):
  overall_summary = "We consider an active contributor in this project to be any contributor who has made at least 1 commit, opened at least 1 issue, or created at least 1 pull request in the past week. \n\n"
  if repo['active_contributors'][-1]['number_of_active_contributors'] == 0:
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
    
  return overall_summary + "\n\n"











if __name__ == '__main__':

  # PART ONE: Setting everything up
  # 1.1: connect to the database 
  engine = create_engine('sqlite:///github.db')

  # 1.2: connect engine to the session
  Session = sessionmaker(bind=engine)
  session = Session()

  # 1.3: output folder + other stuff to run
  newsletter_directory = 'newsletter_data'
  if not os.path.exists(newsletter_directory):
    os.makedirs(newsletter_directory)
  one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
  limit = 100;

  # 1.4: getting all of the repositories
  # query = text("SELECT full_name FROM repositories")
  # result = session.execute(query)
  # repositories = [row[0] for row in result]
  repositories = [
    "tensorflow/tensorflow"
  ]

  # PART TWO: create the markdown for a newsletter
  for repository in repositories:

    # 2.1: call all sort_data.py functions on the repo
    repo_data = {
      "repo_name": repository,
      "open_issues": get_open_issues(session, one_week_ago, repository),
      "closed_issues": get_closed_issues(session, one_week_ago, repository),
      "active_issues": get_active_issues(session, one_week_ago, repository),
      "num_weekly_open_issues": get_num_open_issues_weekly(get_open_issues(session, one_week_ago, repository)),
      "num_weekly_closed_issues": get_num_closed_issues_weekly(get_closed_issues(session, one_week_ago, repository)),
      "issues_by_open_date": sort_issues_open_date(session, repository, limit),
      "issues_by_number_of_comments": sort_issues_num_comments(session, repository, limit),
      "average_issue_close_time": avg_issue_close_time(session, repository),
      "average_issue_close_time_weekly": avg_issue_close_time_weekly(session, one_week_ago, repository),
      "open_pull_requests": get_open_prs(session, one_week_ago, repository),
      "closed_pull_requests": get_closed_prs(session, one_week_ago, repository),
      "active_pull_requests": get_active_prs(session, one_week_ago, repository),
      "num_open_prs": get_num_open_prs(get_open_prs(session, one_week_ago, repository)),
      "num_closed_prs": get_num_closed_prs(get_closed_prs(session, one_week_ago, repository)),
      "commits": get_commit_messages(session, one_week_ago, repository),
      "num_commits": get_num_commits(get_commit_messages(session, one_week_ago, repository)),
      # "first_time_contributors": get_contributors(session, one_week_ago, repository)[0],
      # "active_contributors": get_contributors(session, one_week_ago, repository)[1],
    }
    output_filename = os.path.join(newsletter_directory, f"newsletter_{repository.replace('/', '_')}.txt")

    print(output_filename)
    print(repo_data)
    print(repo_data['repo_name'])
    print(repo_data['open_issues'])
    print(repo_data['closed_issues'])
    print(repo_data['active_issues'])
    print(repo_data['num_weekly_open_issues'])
    print(repo_data['num_weekly_closed_issues'])
    print(repo_data['issues_by_open_date'])
    print(repo_data['issues_by_number_of_comments'])
    print(repo_data['average_issue_close_time'])
    print(repo_data['average_issue_close_time_weekly'])
    print(repo_data['open_pull_requests'])
    print(repo_data['closed_pull_requests'])
    print(repo_data['num_open_prs'])
    print(repo_data['num_closed_prs'])
    print(repo_data['commits'])
    print(repo_data['num_commits'])
    # print(repo_data['first_time_contributors'])
    # print(repo_data['active_contributors'])
    print()

    name = repo_data['repo_name'].split('/')[-1]
    capitalized_name = name[0].upper() + name[1:]

    try:
      with open(output_filename, "w") as outfile:
        
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
        outfile.write("# I. Issues\n\n")

        # 1.1: Open Issues
        outfile.write("## 1.1 Open Issues\n\n")

        # 1.1.1 Open Issues This Week
        outfile.write(f"**Open Issues This Week:** {repo_data.get('num_weekly_open_issues', None)}\n\n")

        # 1.1.2 Issues
        outfile.write("**Summarized Issues:**\n\n")
        # result = open_issues(repo_data)
        # outfile.write(result)


        # 1.2 Top 5 Active Issues
        outfile.write("## 1.2 Top 5 Active Issues:\n\n")
        # result = active_issues(repo_data)
        # outfile.write(result)


        # 1.3 Top 5 Quiet Issues
        outfile.write("## 1.3 Top 5 Quiet Issues:\n\n")
        # result = quiet_issues(repo_data)
        # outfile.write(result)


        # 1.4: Closed Issues
        outfile.write("## 1.4 Closed Issues\n\n")

        # 1.4.1 Closed Issues This Week
        outfile.write(f"**Closed Issues This Week:** {repo_data.get('num_weekly_closed_issues', None)}\n\n")

        # 1.4.2 Average Time to Close Issues This Week
        outfile.write(f"**Average Issue Close Time (This Week):** {repo_data.get('average_issue_close_time_weekly', None)}\n\n")

        # 1.4.3 Average Time to Close Issues All Time
        outfile.write(f"**Average Issue Close Time (All Time):** {repo_data.get('average_issue_close_time', None)}\n\n")

        # 1.4.4 Issues
        outfile.write("**Summarized Issues:**\n\n")
        # result = closed_issues(repo_data)
        # outfile.write(result)


        # 1.5 Issue Discussion Insights
        outfile.write("## 1.5 Issue Discussion Insights\n\n")
        # result = issue_discussion_insights(repo_data)
        # outfile.write(result)

        outfile.write("***\n\n")



        # 2: Pull Requests
        outfile.write("# II. Pull Requests\n\n")

        # 2.1: Open Pull Requests
        outfile.write("## 2.1 Open Pull Requests\n\n")

        # 2.1.1 Open Pull Requests This Week
        outfile.write(f"**Open Pull Requests This Week:** {repo_data.get('num_open_prs', None)}\n\n")

        # 2.1.2 Pull Requests
        outfile.write("**Pull Requests:**\n\n")
        # result = open_pull_requests(repo_data)
        # outfile.write(result)


        # 2.2: Closed Pull Requests
        outfile.write("## 2.2 Closed Pull Requests\n\n")

        # 2.2.1 Closed Pull Requests This Week
        outfile.write(f"**Closed Pull Requests This Week:** {repo_data.get('num_closed_prs', None)}\n\n")

        # 2.2.2 Pull Requests
        outfile.write("**Summarized Pull Requests:**\n\n")
        # result = closed_pull_requests(repo_data)
        # outfile.write(result)


        # 2.3 Pull Request Discussion Insights
        outfile.write("## 2.3 Pull Request Discussion Insights\n\n")
        result = pull_request_discussion_insights(repo_data)
        outfile.write(result)

        outfile.write("***\n\n")



        # 3: Commits
        outfile.write("# III. Commits\n\n")

        # 3.1: Open Commits
        outfile.write("## 3.1 Commits\n\n")

        # 3.1.1 Open Commits This Week
        outfile.write(f"**Commits This Week:** {repo_data.get('num_commits', None)}\n\n")

        # 3.1.2 Commits
        outfile.write("**Summarized Commits:**\n\n")
        # result = commits(repo_data)
        # outfile.write(result)

        outfile.write("***\n\n")



        # 4: Contributors
        outfile.write("# IV. Contributors\n\n")

        # 4.1: Contributors
        outfile.write("## 4.1 Contributors\n\n")

        # print(repo_data.get('first_time_contributors'))
        # print(repo_data.get('active_contributors'))

        # # 4.1.1 New Contributors
        # outfile.write(f"**New Contributors:** {repo_data.get('new_contributors')[-1].get('number_of_new_contributors')}\n\n")

        # # 4.1.2 New Contributors
        # outfile.write(f"**Total Contributors This Week:** {repo_data.get('contributed_this_week')[-1].get('number_of_weekly_contributors')}\n\n")

        # 4.1.4 Active Contributors
        # outfile.write("**Active Contributors:**\n\n")
        # result = active_contributors(repo_data)
        # outfile.write(result)

        outfile.write("\n\n")
      
      print(f"Successfully added {repository} to {output_filename}")

    except Exception as e:
      print(f"Error writing {repository} to {output_filename}")
      print(f"Error code: {e}")
