# This script interacts with LangChain to create markdown files for the newsletters to be sent out
# It uses the data from sort_data.py to insert data into ChatGPT via prompting
# It requires a .env file with an OPENAI_KEY
#hi
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
import re
import time
import random
from openai import RateLimitError
from sort_data import *
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker 
# from prompts.discussion_prompt import discussion_instructions
from prompts import (
   discussion_instructions,
   individual_instructions,
   general_instructions,
   pull_request_instructions,
)

def format_date(iso_str):
   try:
      return datetime.fromisoformat(iso_str.replace('Z', '+00:00')).strftime("%B %d, %Y")
   except Exception:
      return str(iso_str)

load_dotenv()  
API_KEY = os.environ.get("OPENAI_KEY")

# "gpt-3.5-turbo"
prompt_template = "Data: {data}\nInstructions: {instructions}\n"
PROMPT = PromptTemplate(template=prompt_template, input_variables=["data", "instructions"])
llm=ChatOpenAI(model_name="gpt-4.1-mini", temperature=0, openai_api_key = API_KEY)
chain = PROMPT | llm

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

# 1 - Active Issues
def active_issues(repo):
  markdown = "We consider active issues to be issues that that have been commented on most frequently within the last week. Bot comments are omitted. \n\n"
  if not repo.get('active_issues'):
    markdown += "As of our latest update, there are no active issues with ongoing comments this week. \n\n"
    return markdown

  issue_instructions = individual_instructions("an open issue", "issue", "issue", "two detailed sentences")
  issue_instructions += "Do not mention the URL in the summary. Do not mention the labels in the summary. Do NOT add any new lines to the start or end of your summary. In the next line, you MUST give exactly one bullet point that MUST start with EXACTLY three spaces followed by a hyphen and a space ('   - ') summarizing the entire interaction in the comments. This bullet point should be multiple concise sentences, summarizing the ENTIRE comment section. Do not mention specific usernames."
  issues = repo['active_issues'][:5]

  # We are only summarizing the top 5 open issues (active)
  for i, data in enumerate(issues):
    issue_title = data.get('title')
    issue_summary = generate_summary(data, issue_instructions, max_retries=5, base_wait=1)
    issue_summary = issue_summary.strip()  # Trim whitespace and newlines
    issue_url = data.get('url')

    # Format labels as prefix inline
    label_prefix = ""
    if data.get('labels'):
        label_prefix = " ".join([f"[{label['name'].upper()}]" for label in data['labels']]) + " "

    # Make the issue title a clickable link
    markdown += f"{i + 1}. {label_prefix}[**{issue_title}**]({issue_url}): {issue_summary}\n"
    markdown += f"   - Number of comments this week: {data.get('num_comments_this_week')}\n\n"
    

  if (len(issues) < 5):
    markdown += f"Since there were fewer than 5 open issues, all of the open issues have been listed above.\n\n"

  return markdown


# 2 - Stale Issues
def stale_issues(repo):
  markdown = "We consider stale issues to be issues that has had no activity within the last 30 days. The team should work together to get these issues resolved and closed as soon as possible. \n\n"
  if not repo.get('stale_issues'):
    markdown += "As of our latest update, there are no stale issues for the project this week. \n\n"
    return markdown

  issue_instructions = individual_instructions("an open issue", "issue", "issue", "two detailed sentences")
  issue_instructions += "Do not mention the URL in the summary. Do not mention the labels in the summary. Do NOT add any new lines to the start or end of your summary."
  issues = repo['stale_issues'][:5]

  # We are only summarizing the top 5 open issues (stale)
  for i, data in enumerate(issues):
    issue_title = data.get('title')
    issue_summary = generate_summary(data, issue_instructions, max_retries=5, base_wait=1)
    issue_url = data.get('url')

    # Format labels as prefix inline
    label_prefix = ""
    if data.get('labels'):
        label_prefix = " ".join([f"[{label['name'].upper()}]" for label in data['labels']]) + " "

    # Make the issue title a clickable link
    markdown += f"{i + 1}. {label_prefix}[**{issue_title}**]({issue_url}): {issue_summary}\n\n"
    # markdown += f"   - Open for {data.get('time_open')}\n\n"

  if (len(issues) < 5):
    markdown += f"Since there were fewer than 5 stale issues, all of the stale issues have been listed above.\n\n"

  return markdown

# 3 - Open Issues
def open_issues(repo):
  if not repo.get('open_issues'):
    return "As of our latest update, there are no open issues for the project this week.\n\n"

  all_open_issues = ""
  issue_instructions = individual_instructions("an open issue", "issue", "issue", "only one detailed sentence")
  issue_instructions += "Do not mention the labels in the summary. Do NOT add any new lines to the start or end of your summary."
  overall_instructions = general_instructions("issues", "issues", "issues", "issues", True, 2, False)

  # Step 1: get summaries for each open issue first from the llm
  for open_issue in repo['open_issues']:   
    if open_issue.get('body'):
      open_issue['body'] = re.sub(r'<img[^>]*>|\r\n', '', open_issue['body'])
      for comment in open_issue.get('comments', []):
        comment['body'] = re.sub(r'<img[^>]*>|\r\n', '', comment['body'])
    
    issue_summary = generate_summary(open_issue, issue_instructions, max_retries=5, base_wait=1)
    issue_url = f"URL: {open_issue.get('url')}"
    all_open_issues += f"{issue_summary}\n{issue_url}\n\n"

  # Step 2: get markdown output for all open issues 
  overall_summary = generate_summary(all_open_issues, overall_instructions)
  overall_summary = overall_summary.replace("```markdown", "").replace("```", "").strip()

  return overall_summary + "\n"

# 4 - Closed Issues
def closed_issues(repo):
  closed_issues_data = repo['closed_issues']
  
  if not closed_issues_data:
        return "As of our latest update, there were no issues closed in the project this week.\n\n"

  all_closed_issues = ""
  issue_instructions = individual_instructions("a closed issue", "issue", "issue", "only one detailed sentence")
  issue_instructions += "Do not mention the labels in the summary. Do NOT add any new lines to the start or end of your summary."
  overall_instructions = general_instructions("issues", "issues", "issues", "issues", True, 2, False)

  # Step 1: get summaries for each closed issue first from the llm
  for closed_issue in closed_issues_data:
    if closed_issue.get('body'):
      closed_issue['body'] = re.sub(r'<img[^>]*>|\r\n', '', closed_issue['body'])
      for comment in closed_issue.get('comments', []):
        comment['body'] = re.sub(r'<img[^>]*>|\r\n', '', comment['body'])
    
    issue_summary = generate_summary(closed_issue, issue_instructions, max_retries=5, base_wait=1)
    issue_url = f"URL: {closed_issue.get('url')}"
    all_closed_issues += f"{issue_summary}\n{issue_url}\n\n"
  
  # Step 2: get markdown output for all closed issues 
  overall_summary = generate_summary(all_closed_issues, overall_instructions, max_retries=5, base_wait=1)
  overall_summary = overall_summary.replace("```markdown", "").replace("```", "").strip()

  return overall_summary + "\n\n"


# 5 - Issue Discussion Insights
def issue_discussion_insights(repo):
  # Make list of all issues wanting to analyze.
  issue_list = repo['open_issues'] + repo['closed_issues']

  markdown = "This section will analyze the tone and sentiment of discussions within this project's open and closed issues that occurred within the past week. It aims to identify potentially heated exchanges and to maintain a constructive project environment. \n\n"
  
  if not issue_list:
    markdown += "As of our last update, there are no open or closed issues with discussions going on within the past week. \n\n"
    return markdown

  issue_count = 0

  for issue in issue_list:
    instructions = discussion_instructions()

    generated_summary = generate_summary(issue, instructions, max_retries=5, base_wait=1)
    generated_summary_text = str(generated_summary)
  
    # Use regex to capture the summary, score, and reasoning in one line
    pattern = r"(.*?)(?:\s+|,\s*)(0?\.\d+)(?:\s*,\s*|\s+)(.*?)$"
    match = re.search(pattern, generated_summary_text, re.DOTALL)

    if match:
      summary = match.group(1).strip()  # Summary
      score = float(match.group(2).strip())  # Score (float)
      reason = match.group(3).strip()  # Reasoning

      # Add the analysis result to the markdown if score > 0.5
      if score > 0.5:
        issue_count += 1
        markdown += f"{issue_count}. [**{issue['title']}**]({issue['url']})\n"
        markdown += f"   - Toxicity Score: {score:.2f} ({reason})\n"
        markdown += f"   - {summary}\n\n"
    else:
      continue  # Skip this issue if format doesn't match expected

  # If no issues with high toxicity scores
  if issue_count == 0:
      markdown += "Based on our analysis, there are no instances of toxic discussions in the project's open or closed issues from the past week. \n\n"

  return markdown

# 6 - Open Pull Requests
def open_pull_requests(repo):
  if not repo.get('open_pull_requests'):
      return "As of our latest update, there are no open pull requests for the project this week.\n\n"

  # Sort pull requests by the number of commits in descending order
  sorted_pull_requests = sorted(
      repo['open_pull_requests'],
      key=lambda pr: len(pr.get('commits', [])),
      reverse=True
  )

  key_pull_requests = 0
  total_prs = len(sorted_pull_requests)
  key_pull_request_summary = "### Key Open Pull Requests\n\n"
  remaining_pull_requests_summary = ""
  pr_instructions = individual_instructions("an open pull request", "pull request", "pull request", "only one detailed sentence")
  overall_instructions = general_instructions("pull requests", "pull requests", "pull requests", "pull requests", False, 2, True)

  other_pr_count = 0

  for pull_request in sorted_pull_requests:
    if pull_request.get('body'):
      pull_request['body'] = re.sub(r'<img[^>]*>|\r\n', '', pull_request['body'])
      # ensures no merged status is present or used for open PRs
      pull_request.pop('merged', None)

    # Generate the summary for the current open pull request
    pull_request_summary = generate_summary(pull_request, pr_instructions, max_retries=5, base_wait=1)
    pull_request_url = pull_request.get('url')
    pull_request_number = pull_request_url.split('/')[-1]
    shortened_url = f"pull/{pull_request_number}"
    pull_request_title = pull_request.get('title')

    # Process commits
    associated_commits = pull_request.get('commits', [])
    commit_list = ""
    if associated_commits:
      # Extract and format SHA links
      commit_list = ", ".join([f"[{commit['sha'][:5]}]({commit['html_url']})" for commit in associated_commits])

    # Add the first 3 pull requests to the detailed "Key Pull Requests" list
    if key_pull_requests < 3:
      key_pull_request_summary += (
        f"**{key_pull_requests + 1}. {pull_request_title}:** {pull_request_summary}\n"
        f"\n - **URL:** [{shortened_url}]({pull_request_url})\n"
        f"\n - **Associated Commits:** {commit_list}\n\n"
      )
      key_pull_requests += 1
    elif total_prs > 3:
      if other_pr_count < 25:
          summarized_pr_summary = generate_summary(pull_request, pr_instructions, max_retries=5, base_wait=1)
          remaining_pull_requests_summary += f"- {summarized_pr_summary}\n[{shortened_url}]({pull_request_url})\n"
          other_pr_count += 1
      else:
          break

  # Generate "Other Pull Requests" summary only if applicable
  if len(sorted_pull_requests) > 3 and remaining_pull_requests_summary:
    other_pr_summary = generate_summary(remaining_pull_requests_summary, overall_instructions, max_retries=5, base_wait=1)
    if "```markdown" in other_pr_summary:
      start = other_pr_summary.index("```markdown") + len("```markdown")
      end = other_pr_summary.rindex("```")
      other_pr_summary = other_pr_summary[start:end].strip() + "\n"

    # Combine key and other pull request summaries
    all_pull_requests = f"{key_pull_request_summary}\n### Other Open Pull Requests \n\n{other_pr_summary}"
  else:
    all_pull_requests = key_pull_request_summary

  # Return the combined output
  return all_pull_requests + "\n\n"

# 7 - Closed Pull Requests
def closed_pull_requests(repo):
  if not repo.get('closed_pull_requests'):
    return "As of our latest update, there are no closed pull requests for the project this week.\n\n"

  # Sort pull requests by the number of commits in descending order
  sorted_pull_requests = sorted(
      repo['closed_pull_requests'], 
      key=lambda pr: len(pr.get('commits', [])), 
      reverse=True
  )

  total_prs = len(sorted_pull_requests)
  key_pull_requests = 0

  key_pull_request_summary = "### Key Closed Pull Requests\n\n"
  remaining_pull_requests_summary = ""
  pr_instructions = individual_instructions("a closed pull request", "pull request", "pull request", "only one detailed sentence")
  overall_instructions = general_instructions("pull requests", "pull requests", "pull requests", "pull requests", False, 2, True)

  other_pr_count = 0

  for pull_request in sorted_pull_requests:
      if pull_request.get('body'):
          pull_request['body'] = re.sub(r'<img[^>]*>|\r\n', '', pull_request['body'])

      # Generate the summary for the current closed pull request
      pull_request_summary = generate_summary(pull_request, pr_instructions, max_retries=5, base_wait=1)
      pull_request_url = pull_request.get('url')
      pull_request_number = pull_request_url.split('/')[-1]
      shortened_url = f"pull/{pull_request_number}"
      pull_request_title = pull_request.get('title')
      merged_status = pull_request.get('merged')

      # Process commits
      associated_commits = pull_request.get('commits', [])
      commit_list = ""
      if associated_commits:
          # Extract and format SHA links
          commit_list = ", ".join([f"[{commit['sha'][:5]}]({commit['html_url']})" for commit in associated_commits])

      # Add the first 3 closed pull requests to the detailed list
      if key_pull_requests < 3:
        key_pull_request_summary += (
            f"**{key_pull_requests + 1}. {pull_request_title}:** {pull_request_summary}\n"
            f"\n - **URL:** [{shortened_url}]({pull_request_url})\n"
            #f"\n - **Merged:** {merged_status}\n"
            f"\n - **Associated Commits:** {commit_list}\n\n"
        )
        if pull_request.get("merged_at"):
           key_pull_request_summary += f"\n - **Merged:** {format_date(pull_request['merged_at'])}\n"

        key_pull_request_summary += f"\n - **Associated Commits:** {commit_list}\n\n"
        key_pull_requests += 1
      elif total_prs > 3:
        # Limit other closed prs to 25
        if other_pr_count < 25:
            summarized_pr_summary = generate_summary(pull_request, pr_instructions, max_retries=5, base_wait=1)
            remaining_pull_requests_summary += f"- {summarized_pr_summary}\n[{shortened_url}]({pull_request_url})\n"
            other_pr_count += 1
        else:
            break
    
  # Generate "Other Pull Requests" summary only if applicable
  if total_prs > 3 and remaining_pull_requests_summary:
      other_pr_summary = generate_summary(remaining_pull_requests_summary, overall_instructions, max_retries=5, base_wait=1)
      if "```markdown" in other_pr_summary:
          start = other_pr_summary.index("```markdown") + len("```markdown")
          end = other_pr_summary.rindex("```")
          other_pr_summary = other_pr_summary[start:end].strip() + "\n"

      # Combine key and other pull request summaries
      all_pull_requests = f"{key_pull_request_summary}\n### Other Closed Pull Requests \n\n{other_pr_summary}"
  else:
      all_pull_requests = key_pull_request_summary

  # Return the combined output
  return all_pull_requests + "\n\n"

# 8 - Pull Request Discussion Insights
def pull_request_discussion_insights(repo):
  pr_list = repo['open_pull_requests'] + repo['closed_pull_requests']
  markdown = "This section will analyze the tone and sentiment of discussions within this project's open and closed pull requests that occurred within the past week. It aims to identify potentially heated exchanges and to maintain a constructive project environment. \n\n"
  
  if not pr_list:
    markdown += "As of our last update, there are no open or closed pull requests with discussions going on within the past week. \n\n"
    return markdown
  
  pull_request_count = 0

  for pr in pr_list:
    instructions = discussion_instructions()

    generated_summary = generate_summary(pr, instructions, max_retries=5, base_wait=1)
    generated_summary_text = str(generated_summary)
  
    # Use regex to capture the summary, score, and reasoning in one line
    pattern = r"(.*?)(?:\s+|,\s*)(0?\.\d+)(?:\s*,\s*|\s+)(.*?)$"
    match = re.search(pattern, generated_summary_text, re.DOTALL)

    if match:
      summary = match.group(1).strip()  # summary
      score = float(match.group(2).strip())  # score (float)
      reason = match.group(3).strip()  # reasoning

      # Add the analysis result to the markdown if score > 0.5
      if score > 0.5:
        pull_request_count += 1
        markdown += f"{pull_request_count}. [**{pr['title']}**]({pr['url']})\n"
        markdown += f"   - Toxicity Score: {score:.2f} ({reason})\n"
        markdown += f"   - {summary}\n\n"
    else:
        continue  # Skip this PR if the format is incorrect

  if pull_request_count == 0:
      markdown += "Based on our analysis, there are no instances of toxic discussions in the project's open or closed pull requests from the past week. \n\n"
  
  return markdown

# 9 - Active Contributors
def active_contributors(repo):
  overall_summary = "We consider an active contributor in this project to be any contributor who has made at least 1 commit, opened at least 1 issue, created at least 1 pull request, or made more than 2 comments in the last month. \n\n"
  if repo['active_contributors'][-1]['number_of_active_contributors'] == 0:
    overall_summary += "As of our latest update, there are no active contributors for the project this week.\n\n"
    return overall_summary
  else:
    overall_summary += "If there are more than 10 active contributors, the list is truncated to the top 10 based on contribution metrics for better clarity.\n\n"
  
  overall_summary += "Contributor | Commits | Pull Requests | Issues | Comments \n"
  overall_summary += "---|---|---|---|---\n"

  # Step 1: filter out non-contributor entries and aggregate data
  contributors = []
  for contributor in repo['active_contributors']:
    if 'author' in contributor:  # Skip entries without 'author'
      total_activity = contributor['commits'] + contributor['pull_requests'] + contributor['issues'] + contributor['comments']
      contributor['total_activity'] = total_activity
      contributors.append(contributor)

  # Step 2: sort contributors by total_activity in descending order
  sorted_contributors = sorted(contributors, key=lambda x: x['total_activity'], reverse=True)

  # Truncate if list of contributors is > 10 members.
  sorted_contributors = sorted_contributors[:10]

  # Step 3: generate markdown output for all active contributors
  for contributor in sorted_contributors:
    overall_summary += contributor['author'] + " | "
    overall_summary += f"{contributor['commits']}" + " | "
    overall_summary += f"{contributor['pull_requests']}" + " | "
    overall_summary += f"{contributor['issues']}" + " | "
    overall_summary +=f"{contributor['comments']}" + " | \n"
    
  return overall_summary + "\n\n"

# 11 - Last Week's Link
def last_week_link(repo_name):
  # Get shorter repo name
  repo = repo_name.split('/')[1].lower()
  # Get today's date
  today_date = datetime.today()
  # Calculate the date two weeks ago. The link uses the first date of data range, so the last week's link is technically 14 days ago.
  one_week_ago_object = today_date - timedelta(days=14)
  # Format the date with and without the year
  one_week_ago_string_with_year = one_week_ago_object.strftime("%B-%d-%Y").lower()
  one_week_ago_string_without_year = one_week_ago_object.strftime("%B-%d").lower()

  # Create links
  links = [
      f"https://buttondown.com/weekly-project-news/archive/weekly-github-report-for-{repo}-{one_week_ago_string_with_year}/",
      f"https://buttondown.com/weekly-project-news/archive/weekly-github-report-for-{repo}-{one_week_ago_string_without_year}/"
  ]

  # Check links
  for link in links:
    try:
      response = requests.get(link)
      if response.status_code == 200:
        return link
    except requests.RequestException as e:
      print(f"Error checking link: {link}, Error: {e}")

  # If neither link works, return None
  return None

# 12 - Version Summary
def version_summary(repo):
  release_information = [repo.get("release_description"), repo.get("release_create_date")]
  if not release_information:
    return None
  
  instructions = f"Analyze the following version release information, including the description and creation date. Summarize it in 1-2 sentences, focusing on the key updates or changes introduced in this version and any notable highlights or trends. Make sure to incorporate the create date into your summary."
  summary = generate_summary(release_information, instructions)

  return summary + "\n\n"


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

  # DELETE ALL FILES IN NEWSLETTER DIRECTORY IF IT EXISTS
  for filename in os.listdir(newsletter_directory):
     file_path = os.path.join(newsletter_directory, filename)

     # Check if it's a file, rather than a directory
     if os.path.isfile(file_path):
        os.remove(file_path)
        print(f"Deleted newsletter file {file_path}")


  one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
  thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30) 
  limit = 100

  # 1.4: getting all of the repositories
  query = text("SELECT full_name FROM repositories")
  result = session.execute(query)

  repositories = [row[0] for row in result]

  # repositories = ["pytorch/pytorch"]

  # PART TWO: create the markdown for a newsletter
  for repository in repositories:
    # 2.1: call all sort_data.py functions on the repo
    repo_data = get_repo_data(session, one_week_ago, thirty_days_ago, limit, repository)

    output_filename = os.path.join(newsletter_directory, f"newsletter_{repository.replace('/', '_')}.txt")

    name = repo_data['repo_name'].split('/')[-1]
    capitalized_name = name[0].upper() + name[1:]

    try:
      with open(output_filename, "w", encoding='utf-8') as outfile:
        
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

        # 0. Table of Contents
        outfile.write("# Table of Contents\n\n")      
        outfile.write("- [I. News](#news)\n")
        outfile.write("  - [1.1. Recent Version Releases](#releases)\n")
        outfile.write("  - [1.2. Other Noteworthy Updates](#updates)\n")
        outfile.write("- [II. Issues](#issues)\n")
        outfile.write("  - [2.1. Top 5 Active Issues](#active)\n")
        outfile.write("  - [2.2. Top 5 Stale Issues](#stale)\n")
        outfile.write("  - [2.3. Open Issues](#open)\n")
        outfile.write("  - [2.4. Closed Issues](#closed)\n")
        outfile.write("  - [2.5. Issue Discussion Insights](#discussion)\n\n")
        outfile.write("- [III. Pull Requests](#prs)\n")
        outfile.write("  - [3.1. Open Pull Requests](#open-prs)\n")
        outfile.write("  - [3.2. Closed Pull Requests](#closed-prs)\n")
        outfile.write("  - [3.3. Pull Request Discussion Insights](#discussion-prs)\n\n")
        outfile.write("- [IV. Contributors](#contributors)\n")
        outfile.write("  - [4.1. Contributors](#active-contributors)\n\n")
        
        # 1: News
        outfile.write("# <a name='news'></a>I. News\n\n")

        # 1.1 Recent Version Releases
        outfile.write("## <a name='releases'></a>1.1 Recent Version Releases:\n\n")

        latest_release = repo_data.get('latest_release')

        # Check if `latest_release` is not None or an empty dictionary
        if latest_release and latest_release != {}:
            outfile.write(f"The current version of this repository is {latest_release}\n\n")
        else:
            # Skip writing this section if there's no release information
            outfile.write("No recent version releases were found.\n\n")

        # 1.2 Other Noteworthy Updates
        outfile.write("## <a name='updates'></a>1.2 Version Information:\n\n")

        version_info = version_summary(repo_data)
        # Check if version_info has content
        if version_info.strip():
            outfile.write(version_info)
        else:
            # Skip writing this section if version_summary is empty
            outfile.write("No noteworthy version updates were found.\n\n")


        outfile.write("\n\n")

        # 2: Issues
        outfile.write("# <a name='issues'></a>II. Issues\n\n")

        # 2.1 Top 5 Active Issues
        outfile.write("## <a name='active'></a>2.1 Top 5 Active Issues:\n\n")
        result = active_issues(repo_data)
        outfile.write(result)

        # 2.2 Top 5 Stale Issues
        outfile.write("## <a name='stale'></a>2.2 Top 5 Stale Issues:\n\n")
        result = stale_issues(repo_data)
        outfile.write(result)

        # 2.3: Open Issues
        outfile.write("## <a name='open'></a>2.3 Open Issues\n\n")
        outfile.write("This section lists, groups, and then summarizes issues that were created within the last week in the repository. \n\n")

        # 2.3.1 Open Issues This Week
        outfile.write(f"**Issues Opened This Week:** {repo_data.get('num_weekly_open_issues', None)}\n\n")

        # 2.3.2 Summarized Issues (Open)
        outfile.write("**Summarized Issues:**\n\n")
        result = open_issues(repo_data)
        outfile.write(result)

        # 2.4: Closed Issues
        outfile.write("## <a name='closed'></a>2.4 Closed Issues\n\n")
        outfile.write("This section lists, groups, and then summarizes issues that were closed within the last week in the repository. This section also links the associated pull requests if applicable. \n\n")

        # 2.4.1 Closed Issues This Week
        outfile.write(f"**Issues Closed This Week:** {repo_data.get('num_weekly_closed_issues', None)}\n\n")

        # 2.4.3 Summarized Issues (Closed)
        outfile.write("**Summarized Issues:**\n\n")
        result = closed_issues(repo_data)
        outfile.write(result)

        # 2.5 Issue Discussion Insights
        outfile.write("## <a name='discussion'></a>2.5 Issue Discussion Insights\n\n")
        result = issue_discussion_insights(repo_data)
        outfile.write(result)

        outfile.write("***\n\n")

        # 3: Pull Requests
        outfile.write("# <a name='prs'></a>III. Pull Requests\n\n")

        # 3.1: Open Pull Requests
        outfile.write("## <a name='open-prs'></a>3.1 Open Pull Requests\n\n")
        outfile.write("This section provides a summary of pull requests that were opened in the repository over the past week. The top three pull requests with the highest number of commits are highlighted as 'key' pull requests. Other pull requests are grouped based on similar characteristics for easier analysis. Up to 25 pull requests are displayed in this section, while any remaining pull requests beyond this limit are omitted for brevity.\n\n\n\n")

        # 3.1.1 Open Pull Requests This Week
        outfile.write(f"**Pull Requests Opened This Week:** {repo_data.get('num_open_prs', None)}\n\n")

        # 3.1.2 List of Pull Requests (Open)
        result = open_pull_requests(repo_data)
        outfile.write(result)

        # 3.2: Closed Pull Requests
        outfile.write("## <a name='closed-prs'></a>3.2 Closed Pull Requests\n\n")
        outfile.write("This section provides a summary of pull requests that were closed in the repository over the past week. The top three pull requests with the highest number of commits are highlighted as 'key' pull requests. Other pull requests are grouped based on similar characteristics for easier analysis. Up to 25 pull requests are displayed in this section, while any remaining pull requests beyond this limit are omitted for brevity.\n\n")

        # 3.2.1 Closed Pull Requests This Week
        outfile.write(f"**Pull Requests Closed This Week:** {repo_data.get('num_closed_prs', None)}\n\n")

        # 3.2.2 List of Pull Requests (Closed)
        result = closed_pull_requests(repo_data)
        outfile.write(result)

        # 3.3 Pull Request Discussion Insights
        outfile.write("## <a name='discussion-prs'></a>3.3 Pull Request Discussion Insights\n\n")
        result = pull_request_discussion_insights(repo_data)
        outfile.write(result)

        outfile.write("***\n\n")

        # 4: Contributors
        outfile.write("# <a name='contributors'></a>IV. Contributors\n\n")

        # 4.1: Contributors
        outfile.write("## <a name='active-contributors'></a>4.1 Contributors\n\n")

        # 4.1.3 Active Contributors
        outfile.write("**Active Contributors:**\n\n")
        result = active_contributors(repo_data)
        outfile.write(result)

        outfile.write("\n\n\n")

        # 4.1.5 Last Week's Link (if exists)
        link = last_week_link(repository)
        if link:
           outfile.write(f"**Access Last Week's Newsletter: ** \n\n - [Link]({link})")

        outfile.write("\n\n\n")

    except Exception as e:
      print(f"Error writing {repository} to {output_filename}")
      print(f"Error code: {e}")
      continue