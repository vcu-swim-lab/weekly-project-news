from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import requests 
import os 
import sys
from sqlalchemy import create_engine
import logging
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from github import Github
from datetime import datetime, timedelta, timezone
import time
import logging
import pytest
from unittest.mock import MagicMock
os.environ["GITHUB_API_KEYS"] = "testkey123"

# Change path to import tables and anything else
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sort_data
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from tables.commit import Commit

# TASKS TO COMPLETE
# 1. Find way to insert data into test database using dummy repo
# 2. Save the data into a JSON file to easily change the values to test inserts/removals, etc.
# 3. Split across several testing files, like a setup file and then testing file

# TEST FORMAT
# Query database
# Assert expected result (ex. check issue ID, body, etc.)
# Compare to actual result of method


# Create the engine/test db
engine = create_engine('sqlite:///test.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Insert dummy data into database

##### RELEASE TESTS #####

# TEST GET_LATEST_RELEASE
def test_get_latest_release_empty():
    mock = MagicMock()
    mock.query().filter().scalar.return_value = None
    assert sort_data.get_latest_release(mock, 'test/empty-repo') is None

def test_get_latest_release_active():
    mock = MagicMock()
    latest_release = '1.0.0'
    mock.query().filter().scalar.return_value = latest_release
    assert sort_data.get_latest_release(mock, 'test/active-repo') == latest_release

# TEST_GET_RELEASE_DESCRIPTION
def test_get_release_description_empty():
    mock = MagicMock()
    mock.query().filter().scalar.return_value = None
    assert sort_data.get_release_description(mock, 'test/empty-repo') is None

def test_get_release_description_active():
    mock = MagicMock()
    release_description = 'Test description.'
    mock.query().filter().scalar.return_value = release_description
    assert sort_data.get_release_description(mock, 'test/active-repo') == release_description

# TEST_GET_RELEASE_CREATE_DATE
def test_get_release_create_date_empty():
    mock = MagicMock()
    mock.query().filter().scalar.return_value = None
    assert sort_data.get_release_create_date(mock, 'test/empty-repo') is None

def test_get_release_create_date_active():
    mock = MagicMock()
    release_create_date = datetime(2024, 1, 1, 12, 30, 0)
    mock.query().filter().scalar.return_value = release_create_date

    result = sort_data.get_release_create_date(mock, 'test/active-repo')
    assert result == '2024-01-01T12:30:00'


##### ISSUE TESTS #####

# TEST GET_OPEN_ISSUES
def test_get_open_issues_active():
    mock_session = MagicMock()
    one_week_ago = datetime.now() - timedelta(days=7)

    mock_issue = MagicMock()
    mock_issue.repository_full_name = 'test/repo'
    mock_issue.state = 'open'
    mock_issue.created_at = datetime.now()
    mock_issue.user_login = 'username'
    mock_issue.title = 'Issue title'
    mock_issue.body = 'Issue body'
    mock_issue.html_url = 'https://github.com/test/repo/issues/123'
    mock_issue.id = 1

    mock_comment1 = MagicMock()
    mock_comment1.body = 'Comment 1'
    mock_comment2 = MagicMock()
    mock_comment2.body = 'Comment 2'

    mock_session.query().filter().all.side_effect = [
        [mock_issue],                   
        [mock_comment1, mock_comment2] 
    ]

    result = sort_data.get_open_issues(mock_session, one_week_ago, 'test/repo')

    assert len(result) == 1
    assert result[0]['title'] == 'Issue title'
    assert result[0]['body'] == 'Issue body'
    assert result[0]['url'] == 'https://github.com/test/repo/issues/123'
    assert result[0]['comments'][0]['body'] == 'Comment 1'
    assert result[0]['comments'][1]['body'] == 'Comment 2'

# TEST GET_CLOSED_ISSUES
def test_get_closed_issues_active():
    mock_session = MagicMock()
    one_week_ago = datetime.now() - timedelta(days=7)

    mock_issue = MagicMock()
    mock_issue.repository_full_name = 'test/repo'
    mock_issue.state = 'closed'
    mock_issue.created_at = datetime.now()
    mock_issue.user_login = 'username'
    mock_issue.title = 'Issue title'
    mock_issue.body = 'Issue body'
    mock_issue.html_url = 'https://github.com/test/repo/issues/123'
    mock_issue.id = 1

    mock_comment1 = MagicMock()
    mock_comment1.body = 'Comment 1'
    mock_comment2 = MagicMock()
    mock_comment2.body = 'Comment 2'

    mock_session.query().filter().all.side_effect = [
        [mock_issue],                   
        [mock_comment1, mock_comment2] 
    ]

    result = sort_data.get_open_issues(mock_session, one_week_ago, 'test/repo')

    assert len(result) == 1
    issue = result[0]
    assert issue['title'] == 'Issue title'
    assert issue['body'] == 'Issue body'
    assert issue['url'] == 'https://github.com/test/repo/issues/123'
    assert issue['comments'][0]['body'] == 'Comment 1'
    assert issue['comments'][1]['body'] == 'Comment 2'

# TEST GET_ACTIVE_ISSUES
def test_get_active_issues_active():
    mock_session = MagicMock()
    one_week_ago = datetime.now() - timedelta(days=7)

    mock_issue1 = MagicMock()
    mock_issue1.id = 1
    mock_issue1.repository_full_name = 'test/repo'
    mock_issue1.state = 'open'
    mock_issue1.comments = 2
    mock_issue1.created_at = datetime.now()
    mock_issue1.user_login = 'username_1'
    mock_issue1.title = 'Issue 1 Title'
    mock_issue1.body = 'Issue 1 Body'
    mock_issue1.html_url = 'https://github.com/test/repo/issues/1'

    mock_issue2 = MagicMock()
    mock_issue2.id = 2
    mock_issue2.repository_full_name = 'test/repo'
    mock_issue2.state = 'open'
    mock_issue2.comments = 3
    mock_issue2.created_at = datetime.now()
    mock_issue2.user_login = 'username_2'
    mock_issue2.title = 'Issue 2 Title'
    mock_issue2.body = 'Issue 2 Body'
    mock_issue2.html_url = 'https://github.com/test/repo/issues/2'

    mock_issue3 = MagicMock()
    mock_issue3.id = 3
    mock_issue3.repository_full_name = 'test/repo'
    mock_issue3.state = 'open'
    mock_issue3.comments = 1
    mock_issue3.created_at = datetime.now()
    mock_issue3.user_login = 'bot'
    mock_issue3.title = 'Bot Title'
    mock_issue3.body = 'Bot Body'
    mock_issue3.html_url = 'https://github.com/test/repo/issues/3'

    comments1 = [
        MagicMock(user_login='u1', body='Comment A1', created_at=datetime.now() - timedelta(days=1)),
        MagicMock(user_login='u2', body='Comment A2', created_at=datetime.now() - timedelta(days=2)),
    ]

    comments2 = [
        MagicMock(user_login='u3', body='Comment B!', created_at=datetime.now() - timedelta(days=1)),
        MagicMock(user_login='u4', body='Comment B2', created_at=datetime.now() - timedelta(days=2)),
        MagicMock(user_login='u5', body='Comment B3', created_at=datetime.now() - timedelta(days=3)),
    ]

    mock_session.query().filter().all.side_effect = [
        [mock_issue1, mock_issue2],
        comments1,
        comments2
    ]

    result = sort_data.get_active_issues(mock_session, one_week_ago, 'test/repo')

    assert len(result) == 2
    issue1 = result[1] # tests sort works by checking issue1 is 2nd 
    assert issue1['title'] == 'Issue 1 Title'
    assert issue1['body'] == 'Issue 1 Body'
    assert issue1['user'] == 'username_1'
    assert issue1['url'] == 'https://github.com/test/repo/issues/1'
    assert issue1['num_comments_this_week'] == 2
    assert len(issue1['comments']) == 2

    issue2 = result[0]
    assert issue2['title'] == 'Issue 2 Title'
    assert issue2['body'] == 'Issue 2 Body'
    assert issue2['user'] == 'username_2'
    assert issue2['url'] == 'https://github.com/test/repo/issues/2'
    assert issue2['num_comments_this_week'] == 3
    assert len(issue2['comments']) == 3

# TEST GET_STALE_ISSUES
def test_get_stale_issues_active():
    mock_session = MagicMock()
    thirty_days_ago = datetime.now() - timedelta(days=30)

    issue1 = MagicMock()
    issue1.id = 1
    issue1.repository_full_name = 'test/repo'
    issue1.state = 'open'
    issue1.user_login = 'username_1'
    issue1.title = 'Old Issue'
    issue1.body = 'Old Body'
    issue1.updated_at = datetime.now() - timedelta(days=40)
    issue1.created_at = datetime.now() - timedelta(days=45)
    issue1.html_url = 'https://github.com/test/repo/issues/1'

    issue2 = MagicMock()
    issue2.id = 2
    issue2.repository_full_name = 'test/repo'
    issue2.state = 'open'
    issue2.user_login = 'username_2'
    issue2.title = 'Fresh Issue'
    issue2.body = 'Fresh Body'
    issue2.updated_at = datetime.now() - timedelta(days=5)
    issue2.created_at = datetime.now() - timedelta(days=10)
    issue2.html_url = 'https://github.com/test/repo/issues/2'

    mock_session.query().filter().order_by().limit().all.return_value = [issue1]

    result = sort_data.get_stale_issues(mock_session, 'test/repo', thirty_days_ago)

    assert len(result) == 1
    assert result[0]['title'] == 'Old Issue'
    assert '45 days' in result[0]['time_open']
    assert result[0]['url'] == 'https://github.com/test/repo/issues/1'

# TEST GET_NUM_OPEN_ISSUES_WEEKLY
def test_get_num_open_issues_weekly_active():
    issues = [
        {'title': 'Issue 1'},
        {'title': 'Issue 2'},
        {'title': 'Issue 3'}
    ]

    assert sort_data.get_num_open_issues_weekly(issues) == 3

# TEST GET_NUM_CLOSED_ISSUES_WEEKLY
def test_get_num_closed_issues_weekly_active():
    issues = [
        {'title': 'Issue 1'},
        {'title': 'Issue 2'}
    ]

    assert sort_data.get_num_open_issues_weekly(issues) == 2

##### PR TESTS #####

# TEST GET_OPEN_PRS
def test_get_open_prs_active():
    mock_session = MagicMock()
    one_week_ago = datetime.now() - timedelta(days=7)

    pr1 = MagicMock()
    pr1.id = 1
    pr1.repository_full_name = 'test/repo'
    pr1.state = 'open'
    pr1.user_login = 'username_1'
    pr1.created_at = datetime.now() - timedelta(days=5)
    pr1.title = 'PR 1'
    pr1.body = 'PR 1 Body'
    pr1.html_url = 'https://github.com/test/repo/pull/1'

    commit1 = MagicMock()
    commit1.commit_message = 'Commit 1'
    commit1.html_url = 'https://github.com/test/repo/commit/1'
    
    commit2 = MagicMock()
    commit2.commit_message = 'Commit 2'
    commit2.html_url = 'https://github.com/test/repo/commit/2'

    mock_session.query().filter().all.side_effect = [
        [pr1],
        [commit1, commit2]
    ]

    result = sort_data.get_open_prs(mock_session, one_week_ago, 'test/repo')

    assert len(result) == 1
    pr = result[0]
    assert pr['title'] == 'PR 1'
    assert pr['body'] == 'PR 1 Body'
    assert pr['url'] == 'https://github.com/test/repo/pull/1'
    assert len(pr['commits']) == 2
    assert pr['commits'][0]['commit_message'] == 'Commit 1'
    assert pr['commits'][0]['html_url'] == 'https://github.com/test/repo/commit/1'
    assert pr['commits'][1]['commit_message'] == 'Commit 2'
    assert pr['commits'][1]['html_url'] == 'https://github.com/test/repo/commit/2'

# TEST GET_CLOSED_PRS
def test_get_closed_prs_active():
    mock_session = MagicMock()
    one_week_ago = datetime.now() - timedelta(days=7)

    pr1 = MagicMock()
    pr1.id = 1
    pr1.repository_full_name = 'test/repo'
    pr1.state = 'closed'
    pr1.user_login = 'username_1'
    pr1.created_at = datetime.now() - timedelta(days=5)
    pr1.title = 'PR 1'
    pr1.body = 'PR 1 Body'
    pr1.html_url = 'https://github.com/test/repo/pull/1'

    commit1 = MagicMock()
    commit1.commit_message = 'Commit 1'
    commit1.html_url = 'https://github.com/test/repo/commit/1'
    
    commit2 = MagicMock()
    commit2.commit_message = 'Commit 2'
    commit2.html_url = 'https://github.com/test/repo/commit/2'

    mock_session.query().filter().all.side_effect = [
        [pr1],
        [commit1, commit2]
    ]

    result = sort_data.get_open_prs(mock_session, one_week_ago, 'test/repo')

    assert len(result) == 1
    pr = result[0]
    assert pr['title'] == 'PR 1'
    assert pr['body'] == 'PR 1 Body'
    assert pr['url'] == 'https://github.com/test/repo/pull/1'
    assert len(pr['commits']) == 2
    assert pr['commits'][0]['commit_message'] == 'Commit 1'
    assert pr['commits'][0]['html_url'] == 'https://github.com/test/repo/commit/1'
    assert pr['commits'][1]['commit_message'] == 'Commit 2'
    assert pr['commits'][1]['html_url'] == 'https://github.com/test/repo/commit/2'

# TEST GET_NUM_OPEN_PRS
def test_get_num_open_prs_active():
    prs = [
        {'title': 'PR 1'},
        {'title': 'PR 2'},
        {'title': 'PR 3'}
    ]

    assert sort_data.get_num_open_prs(prs) == 3

# TEST GET_NUM_CLOSED_PRS
def test_get_num_closed_prs_active():
    prs = [
        {'title': 'PR 1'},
        {'title': 'PR 2'}
    ]

    assert sort_data.get_num_closed_prs(prs) == 2

##### CONTRIBUTOR TESTS #####

# TEST GET_ACTIVE_CONTRIBUTORS

##### ALL DATA TESTS ####

# TEST GET_REPO_DATA