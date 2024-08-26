# project-news-beacon

This newsletter is AI generated using gpt-4o. It takes data from the GitHub REST API and stores it into a SQLite database. It then takes that data, analyzes and sorts it, and is passed through ChatGPT to create a markdown file. This markdown file is then given to the Buttondown email service which creates the final newsletter in email format. The newsletter is maintained in a CRON job on a Linux server. 

Brief description of files in main:
1. Building the database
The tables folder contains the structured classes for the database tables.

parse_github_data.py makes API calls and inserts data into the database.

update_db.py updates the existing entries in the database.

clean_db.py deletes unnecessary entries from the database

All of these are run on a weekly basis.


2. Analyzing the data
sort_data.py takes data from the database and sorts it into defined categories like open issues, closed issues, open PRs, etc.

3. Creating the newsletter
create_newsletter.py runs the sorted data through ChatGPT and creates a markdown file.

see_all_drafts retrieves specific data related to the Buttondown email service such as drafts.

send_newsletter.py sends the newsletter through Buttondown.


4. Cron jobs
test-run-everything.py runs all of the files above in the correct order. This file is executed on the Linux server.


5. Subscriber data
download_new_subscribers.py retrieves the users who are currently subscribed to the newsletter and outputs a JSON file. This is who we send the newsletters to.

fix_subscribers.py corrects any errors in the subscribers JSON file, such as checking for invalid repository links, incorrect usernames, etc.


6. Testing
test_db.py contains tests for the database (incomplete)


Here is the design document link: https://docs.google.com/document/d/1x6iYWY72xoCQAvC7BRHFbhbi6nzcMLANXl9b2PwW9PQ/edit?usp=sharing
