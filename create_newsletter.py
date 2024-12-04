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
import re


load_dotenv()  

API_KEY = os.environ.get("OPENAI_KEY")

# "gpt-3.5-turbo"
prompt_template = "Data: {data}\nInstructions: {instructions}\n"
PROMPT = PromptTemplate(template=prompt_template, input_variables=["data", "instructions"])
llm=ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key = API_KEY)
chain = PROMPT | llm

# param1: "a closed issue", param2-3: "issue", param4: "only one detailed sentence"
def individual_instructions(param1, param2, param3, param4):
  return f"Above is JSON data describing {param1} from a GitHub project. Give {param4} describing what this {param2} is about, starting with 'This {param3}'. "

# param1-4: "issues", param5: true if should include in instructions
def general_instructions(param1, param2, param3, param4, param5, param6):
  instructions = f"Generate a bulleted list in markdown BASED ON THE DATA ABOVE ONLY where each bullet point starts with a concise topic covered by multiple {param1} in bold text, followed by a colon, followed by a one paragraph summary that must contain {param6} sentences describing the topic's {param2}. This topic, colon, and paragraph summary must all be on the same line on the same bullet point. Do NOT make up content that is not explicitly stated in the data. "
  if param5:
    instructions += f"After each bullet point, there should be indented bullet points giving just the URLs of the {param3} that the topic covers, no other text. Each URL must look like markdown WITHOUT the https://github.com/ in brackets, but only including the https://github.com/ in parentheses (ex. [/topic_type/path_of_link](https://github.com/topic_type/path_of_link)). In the clickable portion of the hyperlink, only include the topic type (issues for issue, pull for pull request) and the path of the link. "
  instructions += f"You must clump {param4} with similar topics together, so there are fewer bullet points. Show the output in markdown in a code block.\n"
  return instructions

# Instructions for pull requests
def pull_request_instructions():
    return """
Generate a one-paragraph summary of the pull request describing its purpose, key changes, and context. 
Do not include specific commit details in this paragraph.

Next, include a bulleted list titled 'Associated Commits' where each bullet point contains the commit message (truncated to 50 characters if needed) 
followed by a hyperlink to the commit's URL in markdown format. 

Use the following format for the list:
**Associated Commits**:

    - [Shortened commit message...](https://github.com/commit/commit_hash)

    - [Another commit message...](https://github.com/commit/another_hash)
    
Do not add extra content or make up data beyond what is provided.
"""


def discussion_instructions():
    return """First, write a one-paragraph summary capturing the trajectory of a GitHub conversation. Be concise and objective, describing usernames, sentiments, tones, and triggers of tension without including specific topics, claims, or arguments. For example, 'username1 expresses frustration that username2's solution did not work'. Start your answer with 'This GitHub conversation'. 
After the summary, on the same line, provide a single number to 2 decimal places on a 0 to 1 scale, indicating the likelihood of toxicity in future comments. Use a scale where:
- 0.0 to 0.3 means very little toxicity,
- 0.3 to 0.6 means a moderate possibility,
- 0.6 to 1.0 means a high likelihood of toxicity.
Do not add any extra text or newlines in this part.
Then, on the same line, provide a brief, comma-separated list of specific reasons for assigning the score. For example, 'Rapid escalation, aggressive language'. Do not include any other details or newlines."""


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



# 1 - Open Issues
def open_issues(repo):
  if not repo.get('open_issues'):
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

    print('a')
    print(issue_summary)
    print('b')

    issue_url = f"URL: {open_issue.get('url')}"
    all_open_issues += f"{issue_summary}\n{issue_url}\n\n"

  print("\n", all_open_issues, "\n\n\n")
  
  # Step 2: get markdown output for all open issues 
  overall_summary = generate_summary(all_open_issues, overall_instructions)
  # if overall_summary.startswith("```") and overall_summary.endswith("```"):
  #   overall_summary = overall_summary[3:-3]
  # if overall_summary.startswith("markdown"):
  #   overall_summary = overall_summary[len("markdown"):].lstrip()
  # if "```markdown" in overall_summary:
  #   start = overall_summary.index("```markdown") + len("```markdown")
  #   end = overall_summary.rindex("```")
  #   overall_summary = overall_summary[start:end].strip() + "\n"

  if "```" in overall_summary:
    overall_summary = overall_summary.replace("```markdown", "").replace("```", "").strip()

  print('c')
  print(overall_summary)
  print('d')

  return overall_summary + "\n"


# 2 - Open Issues (Active)
def active_issues(repo):
  markdown = "We consider active issues to be issues that that have been commented on most frequently within the last week. \n\n"
  if not repo.get('active_issues') or repo.get('active_issues') == []:
    markdown += "As of our latest update, there are no active issues with ongoing comments this week. \n\n"
    return markdown

  issue_instructions = individual_instructions("an open issue", "issue", "issue", "two detailed sentences")
  issue_instructions += "Do not mention the URL in the summary. After that bullet point, you MUST give only one indented bullet point in markdown (which must start with three spaces, then '-') summarizing the entire interaction in the comments. This bullet point should be multiple concise sentences, summarizing the ENTIRE comment section. Do not mention specific usernames."
  issues = repo['active_issues']
  size = min(len(issues), 5)

  # We are only summarizing the top 5 open issues (active)
  for i in range(size):
    data = issues[i]
    issue_title = data.get('title')
    issue_summary = generate_summary(data, issue_instructions, max_retries=5, base_wait=1)
    issue_url = data.get('url')

    # Make the issue title a clickable link
    markdown += f"{i + 1}. [**{issue_title}**]({issue_url}): {issue_summary}\n"
    markdown += f"   - Number of comments this week: {data.get('number_of_comments')}\n\n"
    

  if (size < 5):
    markdown += f"Since there were fewer than 5 open issues, all of the open issues have been listed above.\n\n"

  print("\n", markdown, "\n\n\n")
  return markdown



# 3 - Open Issues (Stale)
def stale_issues(repo):
  markdown = "We consider stale issues to be issues that has had no activity within the last 30 days. The team should work together to get these issues resolved and closed as soon as possible. \n\n"
  if not repo.get('stale_issues'):
    markdown += "As of our latest update, there are no stale issues for the project this week. \n\n"
    return markdown

  issue_instructions = individual_instructions("an open issue", "issue", "issue", "two detailed sentences")
  issue_instructions += "Do not mention the URL in the summary."
  issues = repo['stale_issues']
  size = min(len(issues), 5)

  # We are only summarizing the top 5 open issues (stale)
  for i in range(size):

    data = issues[i]
    issue_title = data.get('title')
    issue_summary = generate_summary(data, issue_instructions, max_retries=5, base_wait=1)
    issue_url = data.get('url')

    # Make the issue title a clickable link
    markdown += f"{i + 1}. [**{issue_title}**]({issue_url}): {issue_summary}\n"
    # markdown += f"   - Open for {data.get('time_open')}\n\n"

  if (size < 5):
    markdown += f"Since there were fewer than 5 open issues, all of the open issues have been listed above.\n\n"

  print("\n", markdown, "\n\n\n")
  return markdown



# 4 - Closed Issues
def closed_issues(repo):
  closed_issues_data = repo['closed_issues']
  
  if not repo.get('closed_issues') or closed_issues_data == []:
        return "As of our latest update, there were no issues closed in the project this week.\n\n"

  all_closed_issues = ""
  issue_instructions = individual_instructions("a closed issue", "issue", "issue", "only one detailed sentence")
  overall_instructions = general_instructions("issues", "issues", "issues", "issues", True, 3)

  # Step 1: get summaries for each closed issue first from the llm
  for closed_issue in closed_issues_data:
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
  # if overall_summary.startswith("```") and overall_summary.endswith("```"):
  #   overall_summary = overall_summary[3:-3]
  # if overall_summary.startswith("markdown"):
  #   overall_summary = overall_summary[len("markdown"):].lstrip()
  # if "```markdown" in overall_summary:
  #   start = overall_summary.index("```markdown") + len("```markdown")
  #   end = overall_summary.rindex("```")
  #   overall_summary = overall_summary[start:end].strip() + "\n"

  if "```" in overall_summary:
    overall_summary = overall_summary.replace("```markdown", "").replace("```", "").strip()
  

  return overall_summary + "\n\n"



# Issue Discussion Insights
def issue_discussion_insights(repo):
    # Make list of all issues wanting to analyze.
    issue_list = repo['open_issues'] + repo['closed_issues']

    markdown = "This section will analyze the tone and sentiment of discussions within this project's open and closed issues that occurred within the past week. It aims to identify potentially heated exchanges and to maintain a constructive project environment. \n\n"
    
    if not issue_list:
        print("No issues to analyze.")
        markdown += "As of our last update, there are no open or closed issues with discussions going on within the past week. \n\n"
        return markdown

    print("Analyzing issues...")
    issue_count = 0

    for issue in issue_list:
        instructions = discussion_instructions()
        print(f"Analyzing issue: {issue}")
    
        generated_summary = generate_summary(issue, instructions, max_retries=5, base_wait=1)
        print(f"Generated summary: \n{generated_summary}")
        
        # Use regular expression to capture the summary, score, and reasoning
        pattern = r"^(.*?)\s+(\d\.\d{2})\s*,?\s*(.*)$"
        match = re.match(pattern, generated_summary.strip())

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
            print(f"Unexpected format in generated summary for issue: {issue['title']}")
            continue  # Skip this issue if format doesn't match expected

    # If no issues with high toxicity scores
    if issue_count == 0:
        markdown += "Based on our analysis, there are no instances of toxic discussions in the project's open issues from the past week. \n\n"

    return markdown
  


# 6 - Open Pull Requests
def open_pull_requests(repo):
  if repo['open_pull_requests'] == []:
    return "As of our latest update, there are no open pull requests for the project this week.\n\n"

  all_pull_requests = ""
  pr_instructions = pull_request_instructions()
  

  # Step 1: get summaries for each open pull request first from the llm
  for pull_request in repo['open_pull_requests']:
    data = pull_request

    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])

    # Process commits related to this PR
    associated_commits = data.get('commits')
    
    commit_list = ""
    if associated_commits:
      commit_list += "\n\n**Associated Commits:**\n\n"
      for commit in associated_commits:
        commit_list += f"- [{commit['commit_message'][:50]}...]({commit['html_url']})\n\n"

    # pull_request_summary = data
    pull_request_summary = generate_summary(data, pr_instructions, max_retries=5, base_wait=1)
    pull_request_url = f"URL: {pull_request.get('url')}"

    # Add processed PR to summary
    all_pull_requests += f"{pull_request_summary}\n{pull_request_url}{commit_list}\n\n"

  print("Printing all pull request information")
  print("\n", all_pull_requests, "\n\n\n")

  # Step 2: get markdown output for all open pull requests 
  overall_summary = generate_summary(all_pull_requests, pr_instructions, max_retries=5, base_wait=1)

  if "```" in overall_summary:
    overall_summary = overall_summary.replace("```markdown", "").replace("```", "").strip()

  return overall_summary + "\n\n"


# 7 - Closed Pull Requests
def closed_pull_requests(repo):
  if repo['closed_pull_requests'] == []:
    return "As of our latest update, there are no closed pull requests for the project this week.\n\n"

  all_pull_requests = ""
  pr_instructions = pull_request_instructions()
  print(pr_instructions)

  # Step 1: get summaries for each closed pull request first from the llm
  for pull_request in repo['closed_pull_requests']:
    data = pull_request
    print(data)

    print(f"Printing data body: {data['body']}")
   
    if (data['body']):
      data['body'] = re.sub(r'<img[^>]*>|\r\n', '', data['body'])

    # Process commits related to this PR
    associated_commits = data.get('commits')
    
    commit_list = ""
    if associated_commits:
      commit_list += "\n\n**Associated Commits:**\n"
      for commit in associated_commits:
        commit_list += f"- [{commit['commit_message'][:50]}...]({commit['html_url']})\n\n"

    # pull_request_summary = data
    pull_request_summary = generate_summary(data, pr_instructions, max_retries=5, base_wait=1)
    pull_request_url = f"URL: {pull_request.get('url')}"

    # Add processed PR to summary
    all_pull_requests += f"{pull_request_summary}\n{pull_request_url}{commit_list}\n\n"

  print("\n", all_pull_requests, "\n\n\n")

  # Step 2: get markdown output for all closed pull requests 
  overall_summary = generate_summary(all_pull_requests, pr_instructions, max_retries=5, base_wait=1)

  if "```" in overall_summary:
    overall_summary = overall_summary.replace("```markdown", "").replace("```", "").strip()

  return overall_summary + "\n\n"



# 8 - Pull Request Discussion Insights
def pull_request_discussion_insights(repo):
    pr_list = repo['open_pull_requests'] + repo['closed_pull_requests']
    print("Printing pr_list")
    print(pr_list)

    markdown = "This section will analyze the tone and sentiment of discussions within this project's open and closed pull requests that occurred within the past week. It aims to identify potentially heated exchanges and to maintain a constructive project environment. \n\n"
    
    if not pr_list:
        markdown += "As of our last update, there are no open or closed pull requests with discussions going on within the past week. \n\n"
        return markdown
    
    pull_request_count = 0
    count = 0

    for pr in pr_list:
        instructions = discussion_instructions()

        generated_summary = generate_summary(pr, instructions, max_retries=5, base_wait=1)
        print(f"Generated summary to analyze: \n{generated_summary}")
        
        # Use regex to capture the summary, score, and reasoning in one line
        pattern = r"^(.*?)\s+(\d\.\d{2})\s*,?\s*(.*)$"
        match = re.match(pattern, generated_summary.strip())

        if match:
            summary = match.group(1).strip()  # summary
            score = float(match.group(2).strip())  # score (float)
            reason = match.group(3).strip()  # reasoning

            print("Summary:", summary)
            print("Score:", score)
            print("Reason:", reason)

            # Add the analysis result to the markdown if score > 0.5
            if score > 0.5:
                pull_request_count += 1
                markdown += f"{pull_request_count}. [**{pr['title']}**]({pr['url']})\n"
                markdown += f"   - Toxicity Score: {score:.2f} ({reason})\n"
                markdown += f"   - {summary}\n\n"
        else:
            print(f"Unexpected format in generated summary for PR: {pr['title']}")
            continue  # Skip this PR if the format is incorrect

    if pull_request_count == 0:
        markdown += "Based on our analysis, there are no instances of toxic discussions in the project's open pull requests from the past week. \n\n"
    
    return markdown




# def general_instructions(param1, param2, param3, param4, param5, param6):
#   instructions = f"Generate a bulleted list in markdown BASED ON THE DATA ABOVE ONLY where each bullet point starts with a concise topic covered by multiple {param1} in bold text, followed by a colon, followed by a one paragraph summary that must contain {param6} sentences describing the topic's {param2}. This topic, colon, and paragraph summary must all be on the same line on the same bullet point. Do NOT make up content that is not explicitly stated in the data. "
#   if param5:
#     instructions += f"After each bullet point, there should be indented bullet points giving just the URLs of the {param3} that the topic covers, no other text. Each URL must look like markdown WITHOUT the https:// in brackets, but only including the https:// in parentheses (ex. [github.com/...](https://github.com/...) ). "
#   instructions += f"You must clump {param4} with similar topics together, so there are fewer bullet points. Show the output in markdown in a code block.\n"
#   return instructions


# 9 - Commits
def commits(repo):
  if repo['commits'] == []:
    return "As of our latest update, there are no commits for the project this week.\n\n"

  all_commits = ""
  commit_instructions = individual_instructions("a commit", "commit", "commit", "only one detailed sentence")
  overall_instructions = """You are an expert software developer with deep knowledge of this GitHub project. I have a list of the most recent commits to the project. Your task is to:

1. Carefully read and understand all of the commits.
2. Identify common themes, areas of development, or types of changes across these commits.
3. Group the commits into at most 25 broad topics that collectively cover all of the commits.
4. For each topic, write a summary that encapsulates the main ideas from all related commits.

Present your analysis as a markdown bulleted list where each bullet point:
- Starts with the topic name in bold
- Is followed by a colon
- Contains a 2-sentence summary covering multiple related commits

Important notes:
- Every single commit must be accounted for in your groupings.
- Do not create a separate topic for each commit. Each topic should cover multiple related commits.
- Ensure your summary sentences for each topic reflect changes from various commits, not just one.

Example format:
- **Dispatch Optimization**: A redundant bounds check has been removed from the code since the condition is already verified in the EvaluateEpilogue function. Profiling observations also indicate that tp_richcompare is marginally faster to dispatch than eq.

Provide your comprehensive analysis of all of the commits, generated as a bulleted list in markdown as described above."""


  # Step 1: get summaries for each commit first from the llm
  number = 1
  for commit in repo['commits']:
    data = commit
    
    if (data['message']):
      data['message'] = re.sub(r'<img[^>]*>|\r\n', '', data['message'])

    # commit_summary = data
    commit_summary = generate_summary(data, commit_instructions, max_retries=5, base_wait=1)
    all_commits += f"{number}. {commit_summary}\n"
    number += 1

  print("\n", all_commits, "\n\n\n")

  # Step 2: get markdown output for all commits
  overall_summary = generate_summary(all_commits, overall_instructions, max_retries=5, base_wait=1)
  # if overall_summary.startswith("```markdown"):
  #   overall_summary = overall_summary[len("```markdown"):].lstrip()
  # if overall_summary.startswith("```"):
  #   overall_summary = overall_summary[3:].lstrip()
  # if overall_summary.endswith("```"):
  #   overall_summary = overall_summary[:-3].rstrip()
  # if overall_summary.startswith("markdown"):
  #   overall_summary = overall_summary[len("markdown"):].lstrip()
  if "```markdown" in overall_summary:
    start = overall_summary.index("```markdown") + len("```markdown")
    end = overall_summary.rindex("```")
    overall_summary = overall_summary[start:end].strip() + "\n"
    
  return overall_summary + "\n\n"



# 10 - Active Contributors
def active_contributors(repo):
  overall_summary = "We consider an active contributor in this project to be any contributor who has made at least 1 commit, opened at least 1 issue, created at least 1 pull request, or made more than 2 comments in the last month. \n\n"
  if repo['active_contributors'][-1]['number_of_active_contributors'] == 0:
    overall_summary += "As of our latest update, there are no active contributors for the project this week.\n\n"
    return overall_summary
  
  print(len(repo['active_contributors']))

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
  if (len(sorted_contributors) > 10):
        sorted_contributors = sorted_contributors[:10]

  # Step 3: generate markdown output for all active contributors
  for contributor in sorted_contributors:
    overall_summary += contributor['author'] + " | "
    overall_summary += f"{contributor['commits']}" + " | "
    overall_summary += f"{contributor['pull_requests']}" + " | "
    overall_summary += f"{contributor['issues']}" + " | "
    overall_summary +=f"{contributor['comments']}" + " | \n"
    
  return overall_summary + "\n\n"


def lastWeekLink(repo_name):
    # Get today's date
    today_date = datetime.today()
    # Calculate the date one week ago
    one_week_ago_object = today_date - timedelta(days=7)
    # Format the date as a string in "YYYY-MM-DD" format
    one_week_ago_string = one_week_ago_object.strftime("%Y-%m-%d")
    # Create the new link
    link = f"https://buttondown.com/weekly-project-news/archive/weekly-github-report-for-{repo_name}-{one_week_ago_string}/"
    return link


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
  thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30) 
  limit = 100;

  # 1.4: getting all of the repositories
  query = text("SELECT full_name FROM repositories")
  result = session.execute(query)

  # repositories = [row[0] for row in result]
  repositories = [
    # "ggerganov/llama.cpp",
    # "nodejs/node",
    # "openxla/xla",
    # "stevenbui44/flashcode",
    "cnovalski1/APIexample",
    "tensorflow/tensorflow",
    "monicahq/monica"
  ]


  # PART TWO: create the markdown for a newsletter
  for repository in repositories:

    # print('a')
    # print(repository)
    # print('b')
    repo_name = repository

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
        outfile.write("  - [1.2. Other Noteworthy Updates](#updates)\n\n")
        outfile.write("- [II. Issues](#issues)\n")
        outfile.write("  - [2.1. Top 5 Active Issues](#active)\n")
        outfile.write("  - [2.2. Top 5 Stale Issues](#stale)\n")
        outfile.write("  - [2.3. Open Issues](#open)\n")
        outfile.write("  - [2.4. Closed Issues](#closed)\n\n")
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
        
        if latest_release is not {}:
          outfile.write(f"The current version of this repository is {latest_release}\n\n")

        # 1.2 Other Noteworthy Updates
        outfile.write("## <a name='updates'></a>1.2 Other Noteworthy Updates:\n\n")
        # TODO Add code for analyzing the README file.


        # 2: Issues
        outfile.write("# <a name='issues'></a>II. Issues\n\n")

        # 2.1 Top 5 Active Issues
        outfile.write("## <a name='active'></a>2.1 Top 5 Active Issues:\n\n")
        result = active_issues(repo_data)
        outfile.write(result)


        # 2.2 Top 5 Stale Issues
        outfile.write("## <a name='stale'></a>2.2 Top 5 Stale Issues:\n\n") # Changed to STALE instead of quiet
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
        outfile.write("This section lists and summarizes pull requests that were created within the last week in the repository. \n\n")

        # 3.1.1 Open Pull Requests This Week
        outfile.write(f"**Pull Requests Opened This Week:** {repo_data.get('num_open_prs', None)}\n\n")

        # 3.1.2 List of Pull Requests (Open)
        outfile.write("**Pull Requests:**\n\n")
        result = open_pull_requests(repo_data)
        outfile.write(result)


        # 3.2: Closed Pull Requests
        outfile.write("## <a name='closed-prs'></a>3.2 Closed Pull Requests\n\n")
        outfile.write("This section lists and summarizes pull requests that were closed within the last week in the repository. Similar pull requests are grouped, and associated commits are linked if applicable. \n\n")

        # 3.2.1 Closed Pull Requests This Week
        outfile.write(f"**Pull Requests Closed This Week:** {repo_data.get('num_closed_prs', None)}\n\n")

        # 3.2.2 List of Pull Requests (Closed)
        outfile.write("**Summarized Pull Requests:**\n\n")
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

        outfile.write("\n\n")

        # 4.1.4 Last Week's Link (if exists)
        if check_link_works(lastWeekLink( repo_name)): 
          outfile.write("Access last week's newsletter: " + lastWeekLink( repo_name))

        outfile.write("\n\n")

        
      
      print(f"Successfully added {repository} to {output_filename}")

    except Exception as e:
      print(f"Error writing {repository} to {output_filename}")
      print(f"Error code: {e}")
