import sqlite3
from github import Github
from datetime import datetime, timedelta, timezone
import time
import json
import os
import requests
from dotenv import load_dotenv
import concurrent.futures
import multiprocessing
from acquire_project_data import *
from enum import Enum

# Script to update repositories.db
# Connect to the database
conn = sqlite3.connect('repositories.db')
cursor = conn.cursor()

# Create issues table
create_issues_query = """
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER,
    issue_id INTEGER,
    repository_url VARCHAR(255),
    issue_url VARCHAR(255),
    state VARCHAR(255),
    user_login VARCHAR(255),
    labels JSON,
    created_at DATETIME,
    updated_at DATETIME,
    closed_at DATETIME,
    comments JSON,
    num_comments INTEGER
);
"""
cursor.execute(create_issues_query)
conn.commit()

# Create commits table
create_commits_query = """
CREATE TABLE IF NOT EXISTS commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER,
    commit_sha VARCHAR(255),
    commit_message TEXT,
    commit_author_login VARCHAR(255),
    commit_author_url VARCHAR(255),
    commit_url VARCHAR(255),
    commit_date DATETIME
);
"""
cursor.execute(create_commits_query)
conn.commit()


# Create pull requests table
create_prs_query = """
CREATE TABLE IF NOT EXISTS pull_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER,
    pr_id INTEGER,
    pr_state VARCHAR(255),
    pr_title TEXT,
    pr_body TEXT,
    pr_user_login VARCHAR(255),
    pr_user_url VARCHAR(255),
    pr_labels JSON,
    pr_url VARCHAR(255),
    pr_comments JSON
);
"""
cursor.execute(create_prs_query)
conn.commit()

# Create contributors table
create_contributors_query = """
CREATE TABLE IF NOT EXISTS contributors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER,
    contributor_login VARCHAR(255),
    contributor_url VARCHAR(255),
    contributions INTEGER
);
"""
cursor.execute(create_contributors_query)
conn.commit()
