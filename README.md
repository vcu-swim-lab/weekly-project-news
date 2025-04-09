# Weekly Project News

A weekly AI-generated newsletter that highlights updates from open-source GitHub repositories in email format. 

---

### Automatically Curated From GitHub  
Weekly Project News uses the GitHub REST API to gather recent repository activity including pull requests, issues, and contributions. This data is inserted into a SQLite database, sorted, categorized, and sent through GPT-4o to generate human-readable summaries.

Stay informed on your favorite projects without all of the noise.


![Newsletter Sign-Up Screen](/screenshots/newsletterSignup.PNG)
---

### Powered by GPT-4o for Smart Summaries  
GPT-4o analyzes changes, organizes content into categories, and writes a markdown newsletter that feels like it was hand-crafted by a developer. The result is a structured email highlighting what’s new and what matters.


![Newsletter Draft Screenshot](/screenshots/newsletterMarkdown.PNG)

---

### Delivery via Buttondown  
After generation, the newsletter is automatically delivered through the Buttondown email service. Everything runs on a weekly CRON job hosted on a Linux server with no manual intervention required.


![Newsletter Email Screenshot](/screenshots/newsletterEmail.PNG)

---

### How It Works

#### Building the Database
- `tables/` – Contains the SQLAlchemy table definitions for GitHub entities  
- `parse_github_data.py` – Fetches data from the GitHub REST API and populates the database  
- `update_db.py` – Keeps repository data up to date  
- `clean_db.py` – Removes stale or unnecessary records  

#### Analyzing the Data
- `sort_data.py` – Sorts entries by categories like open issues, closed PRs, etc.  

#### Creating the Newsletter
- `create_newsletter.py` – Passes sorted data through GPT-4o to generate a markdown file  
- `see_all_drafts.py` – Retrieves drafts from Buttondown  
- `send_newsletter.py` – Sends the completed newsletter  

#### Subscriber Management
- `download_new_subscribers.py` – Retrieves and outputs current subscribers  
- `fix_subscribers.py` – Cleans up invalid usernames, repo links, etc.  

#### Orchestration
- `test-run-everything.py` – Runs the full workflow in order via CRON  

---

### Testing (In Progress)
- `test_db.py` – Unit tests for database integrity and insertions

---

### Developed By\

**Christian Novalski, Steven Bui, Audrey Lewis**

(Virginia Commonwealth University, NSF REU - SWIM Lab)


**Dr. Kostadin Damevski, Project Originator & Faculty Advisor**

(Virginia Commonwealth University - SWIM Lab)


**Other Contributors:**\


**Ghalian Fayyadh, Damian Ashjian, Christopher Chavez**

(Virginia Commonwealth University - SWIM Lab)

---

### Subscribe  
Want to receive the newsletter?  
Sign up here: https://buttondown.com/weekly-project-news

---
