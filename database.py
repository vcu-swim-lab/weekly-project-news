# import mysql.connector
import json
# import os
import sqlite3
# from databases import Database
# import asyncio

class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        db_cursor = self.conn.cursor()

        db_cursor.execute(
            "CREATE TABLE IF NOT EXISTS repositories ( \
            id INT AUTO_INCREMENT PRIMARY KEY, \
            repo_name VARCHAR(255) NOT NULL UNIQUE, \
            open_issues JSON, \
            closed_issues JSON, \
            active_issues JSON, \
            num_weekly_open_issues INT, \
            num_weekly_closed_issues INT, \
            issues_by_open_date JSON, \
            issues_by_number_of_comments JSON, \
            average_issue_close_time VARCHAR(255), \
            average_issue_close_time_weekly VARCHAR(255), \
            open_pull_requests JSON, \
            closed_pull_requests JSON, \
            num_open_prs INT, \
            num_closed_prs INT, \
            commits JSON, \
            num_commits INT, \
            new_contributors JSON, \
            contributed_this_week JSON, \
            active_contributors JSON)"
        )

    def insert_repositories_table(self, json_data):
        db_cursor = self.conn.cursor()
        
        def safe_get(data, key):
            return data.get(key, None) 

        data_to_insert = (
            safe_get(json_data, "repo_name"),
            json.dumps(safe_get(json_data, "open_issues")) if safe_get(json_data, "open_issues") is not None else None,
            json.dumps(safe_get(json_data, "closed_issues")) if safe_get(json_data, "closed_issues") is not None else None,
            json.dumps(safe_get(json_data, "active_issues")) if safe_get(json_data, "active_issues") is not None else None,
            safe_get(json_data, "num_weekly_open_issues"),
            safe_get(json_data, "num_weekly_closed_issues"),
            json.dumps(safe_get(json_data, "issues_by_open_date")) if safe_get(json_data, "issues_by_open_date") is not None else None,
            json.dumps(safe_get(json_data, "issues_by_number_of_comments")) if safe_get(json_data, "issues_by_number_of_comments") is not None else None,
            safe_get(json_data, "average_issue_close_time"),
            safe_get(json_data, "average_issue_close_time_weekly"),
            json.dumps(safe_get(json_data, "open_pull_requests")) if safe_get(json_data, "open_pull_requests") is not None else None,
            json.dumps(safe_get(json_data, "closed_pull_requests")) if safe_get(json_data, "closed_pull_requests") is not None else None,
            safe_get(json_data, "num_open_prs"),
            safe_get(json_data, "num_closed_prs"),
            json.dumps(safe_get(json_data, "commits")) if safe_get(json_data, "commits") is not None else None,
            safe_get(json_data, "num_commits"),
            json.dumps(safe_get(json_data, "new_contributors")) if safe_get(json_data, "new_contributors") is not None else None,
            json.dumps(safe_get(json_data, "contributed_this_week")) if safe_get(json_data, "contributed_this_week") is not None else None,
            json.dumps(safe_get(json_data, "active_contributors")) if safe_get(json_data, "active_contributors") is not None else None
        )

        try:
            # print(data_to_insert)
            db_cursor.execute("INSERT INTO repositories (repo_name, \
                open_issues, \
                closed_issues, \
                active_issues, \
                num_weekly_open_issues, \
                num_weekly_closed_issues, \
                issues_by_open_date, \
                issues_by_number_of_comments, \
                average_issue_close_time, \
                average_issue_close_time_weekly, \
                open_pull_requests, \
                closed_pull_requests, \
                num_open_prs, \
                num_closed_prs, \
                commits, \
                num_commits, \
                new_contributors, \
                contributed_this_week, \
                active_contributors) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                data_to_insert,)
            self.conn.commit()
            print("Inserted repository")
        except Exception as e: 
            print(e)
            self.conn.rollback()  # Rollback the transaction


    def fetch_repo(self, repo):
        query = f"SELECT COUNT(*) FROM repositories WHERE repo_name = ?"
        db_cursor = self.conn.cursor()
        db_cursor.execute(query, (repo,))
        result = db_cursor.fetchone()[0]
        return result

    def close(self):
        self.conn.close()