from unittest.mock import MagicMock
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

# Change path to import tables and anything else
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from tables.commit import Commit
from sort_data import *

one_week_ago = datetime.now() - timedelta(days=7)
thirty_days_ago = datetime.now() - timedelta(days=30)
now = datetime.now()


# Setup mock fixture
@pytest.fixture
def mock_session_fixture(mocker):
    mock_session = mocker.Mock()
    mock_query = mocker.Mock()
    mock_filter = mocker.Mock()

    mock_query.filter.return_value = mock_filter

    return {
        "session": mock_session,
        "query": mock_query,
        "filter": mock_filter
    }

##### RELEASE TESTS #####
# get_latest_release tests
@pytest.mark.parametrize("repo_name, expected, func, test_case", [
    ("owner/repo", "v2.3.1", get_latest_release, "T1"),  # T1: Exists, has info, valid data
    ("owner/repo_invalid", "", get_latest_release, "T2"),  # T2: Exists, has info, invalid data
    ("valid_repo_no_release", None, get_latest_release, "T3"),  # T3: Exists, no info, valid data
    ("valid_repo_no_release", None, get_latest_release, "T4"),  # T4: Exists, no info, invalid data
    ("nonexistent_repo", "v1.0.0", get_latest_release, "T5"),  # T5: Doesn't exist, has info, valid data
    ("nonexistent_repo", "", get_latest_release, "T6"),  # T6: Doesn't exist, has info, invalid data
    ("nonexistent_repo", None, get_latest_release, "T7"),  # T7: Doesn't exist, no info, valid data
    ("", None, get_latest_release, "T8"),  # T8: Doesn't exist, no info, invalid data
    (None, None, get_latest_release, "T9"),  # T9: Empty test case

    # get_release_description tests
    ("owner/repo", "Initial release", get_release_description, "T1"),  # T1: Exists, has info, valid data
    ("owner/repo_invalid", "", get_release_description, "T2"),  # T2: Exists, has info, invalid data
    ("valid_repo_no_desc", None, get_release_description, "T3"),  # T3: Exists, no info, valid data
    ("valid_repo_no_desc", None, get_release_description, "T4"),  # T4: Exists, no info, invalid data
    ("nonexistent_repo", "Some description", get_release_description, "T5"),  # T5: Doesn't exist, has info, valid data
    ("nonexistent_repo", "", get_release_description, "T6"),  # T6: Doesn't exist, has info, invalid data
    ("nonexistent_repo", None, get_release_description, "T7"),  # T7: Doesn't exist, no info, valid data
    ("a" * 300, None, get_release_description, "T8"),  # T8: Doesn't exist, no info, invalid data
    (None, None, get_release_description, "T9"),  # T9: Empty test case

    # get_release_create_date tests
    ("owner/repo", "2024-01-01T12:00:00", get_release_create_date, "T1"),  # T1: Exists, has info, valid data
    ("owner/repo_invalid", "invalid-date", get_release_create_date, "T2"),  # T2: Exists, has info, invalid data
    ("valid_repo_no_date", None, get_release_create_date, "T3"),  # T3: Exists, no info, valid data
    ("valid_repo_no_date", None, get_release_create_date, "T4"),  # T4: Exists, no info, invalid data
    ("nonexistent_repo", "2024-02-15T08:30:00", get_release_create_date, "T5"),  # T5: Doesn't exist, has info, valid data
    ("nonexistent_repo", "invalid-date", get_release_create_date, "T6"),  # T6: Doesn't exist, has info, invalid data
    ("nonexistent_repo", None, get_release_create_date, "T7"),  # T7: Doesn't exist, no info, valid data
    ("owner|repo", None, get_release_create_date, "T8"),  # T8: Doesn't exist, no info, invalid data
    (None, None, get_release_create_date, "T9"),  # T9: Empty test case
])
def test_release_functions(mock_session_fixture, repo_name, expected, func, test_case):
    # Set up the mock return value based on the function being tested
    mock_session_fixture["filter"].scalar.return_value = (
        expected if func != get_release_create_date else _mock_datetime(expected) if expected else None
    )
    mock_session_fixture["session"].query.return_value = mock_session_fixture["query"]
    mock_session_fixture["query"].filter.return_value = mock_session_fixture["filter"]

    result = func(mock_session_fixture["session"], repo_name)
    assert result == expected, f"Failed test case {test_case} for function {func.__name__}"


def _mock_datetime(date_string):
    from datetime import datetime
    class MockDate:
        def isoformat(self):
            return date_string
    return MockDate()


##### ISSUE TESTS #####

# TEST GET_OPEN_ISSUES AND GET_CLOSED_ISSUES
@pytest.mark.parametrize("func, repo_name, time_param, issue_state, expected_issues, expected_result, username, bot_status, test_case", [
    # T1: Open issues, less than one week ago, bot user
    # Expected to return empty array because of bot
    (get_open_issues, "owner/repo", one_week_ago, 'open', 0, [], "ci-bot[bot]", "Bot", "T1"),

    # T2: Open issues, less than one week ago, no bot
    (get_open_issues, "owner/repo", one_week_ago, 'open', 1, [{"title": "Open Issue 1", "body": "Description", "url": "http://open_issue1.url", "comments": []}], "developer", "No Bot", "T2"),
    
    # T3: Open issues, more than one week ago, bot user
    # Expected to return empty array
    (get_open_issues, "owner/repo", thirty_days_ago, 'open', 0, [], "github-bot", "Bot", "T3"),
    
    # T4: Open issues, more than one week ago, no bot
    # Expected to return empty array
    (get_open_issues, "owner/repo", thirty_days_ago, 'open', 0, [],"developer", "No Bot", "T4"),
    
    # T6: Closed issues, less than one week ago, no bot
    (get_closed_issues, "owner/repo", one_week_ago, 'closed', 1, [{"title": "Closed Issue 1", "body": "Description", "url": "http://closed_issue1.url", "comments": []}], "developer", "No Bot", "T6"),
    
    # T5: Closed issues, less than one week ago, bot user
    # Expected to return empty array
    (get_closed_issues, "owner/repo", one_week_ago, 'closed', 1, [], "dependabot[bot]", "Bot", "T5"),
    
    # T7: Closed issues, more than one week ago, bot user
    # Expected to return empty array because of bot
    (get_closed_issues, "owner/repo", thirty_days_ago, 'closed', 1, [], "ai-bot", "Bot", "T7"),
    
    # T8: Closed issues, more than one week ago, no bot
    # Expected to return empty array becaue of date
    (get_closed_issues, "owner/repo", thirty_days_ago, 'closed', 1, [],"developer", "No Bot", "T8"),
    
    # T9: Empty case
    # Expected to return empty array
    (get_open_issues, "owner/repo", one_week_ago, 'open', 0, [], None, "No issue just empty", "T9"),
    
    # Active issues tests
    # Needs to check comments within time window
    (get_active_issues, "owner/repo", one_week_ago, 'open', 2, [{"title": "Active Issue 1", "body": "Description", "user": "developer", "url": "http://active_issue1.url", "comments": [{"body": "Recent comment"}], "num_comments_this_week": 1}], "developer", "No Bot", "Active Issues Test"),
    
    # Stale issues tests
    (get_stale_issues, "owner/repo", thirty_days_ago, 'open', 1, [{"title": "Stale Issue", "time_open": "45 days, 00 hours, 00 minutes", "last_updated": thirty_days_ago - timedelta(days=15), "body": "Description", "url": "http://stale_issue.url", "id": 1}], "developer", "No Bot", "Stale Issues Test"),
    
    # Numeric functions tests
    # Function just returns the length
    (get_num_open_issues_weekly, "owner/repo", one_week_ago, 'open', 3, 3,"developer", "No Bot", "Count Open Issues Test"),
    
    # Function just returns the length
    (get_num_closed_issues_weekly, "owner/repo", one_week_ago, 'closed', 2, 2,"developer", "No Bot", "Count Closed Issues Test"),
])
def test_issue_functions(mock_session_fixture, mocker, func, repo_name, time_param, issue_state, 
                       expected_issues, expected_result, username, bot_status, test_case):
    
    # Handle numeric functions separately
    if func in [get_num_open_issues_weekly, get_num_closed_issues_weekly]:
        mock_list = [mocker.Mock() for _ in range(expected_result)]
        result = func(mock_list)
        assert result == expected_result
        return
    
    # Set up base mock objects
    mock_session_fixture["session"].query.return_value = mock_session_fixture["query"]
    mock_session_fixture["query"].filter.return_value = mock_session_fixture["filter"]
    mock_session_fixture["filter"].order_by.return_value = mock_session_fixture["filter"]
    mock_session_fixture["filter"].limit.return_value = mock_session_fixture["filter"]
    if expected_issues == 0:
        mock_session_fixture["filter"].all.return_value = []
        result = func(mock_session_fixture["session"], time_param, repo_name)
        assert result == expected_result
        return
    
    # Prepare mock issues
    mock_issues = []
    is_bot = username and ("bot" in username.lower() or "[bot]" in username.lower())
    
    for i in range(expected_issues):
        issue = mocker.Mock()
        issue.repository_full_name = repo_name
        issue.state = issue_state
        issue.user_login = username if username else "regular_user"
        issue.id = i + 1
        
        # Configure dates based on function and test case
        if test_case in ["T1", "T2", "T5", "T6"]:
            if issue_state == 'open':
                issue.created_at = one_week_ago + timedelta(days=1)
            else:
                issue.closed_at = one_week_ago + timedelta(days=1)
        elif test_case in ["T3", "T4", "T7", "T8"]:
            if issue_state == 'open':
                issue.created_at = one_week_ago - timedelta(days=5)
            else:
                issue.closed_at = one_week_ago - timedelta(days=5)
        
        # Special config for stale functions
        if func == get_stale_issues:
            issue.created_at = datetime.now() - timedelta(days=45)
            issue.updated_at = thirty_days_ago - timedelta(days=15)
            issue.title = "Stale Issue"
            issue.body = "Description"
            issue.html_url = "http://stale_issue.url"
        elif isinstance(expected_result, list) and i < len(expected_result):
            if "title" in expected_result[i]:
                issue.title = expected_result[i]["title"]
                issue.body = expected_result[i].get("body", "")
                issue.html_url = expected_result[i].get("url", "")
        
        mock_issues.append(issue)
    
    # Set up side effects based on function type
    if func == get_active_issues:
        comments = []
        if isinstance(expected_result, list) and len(expected_result) > 0:
            for comment_data in expected_result[0].get("comments", []):
                comment = mocker.Mock()
                comment.body = comment_data.get("body", "")
                comment.created_at = time_param + timedelta(hours=1)
                comment.user_login = username if username else "regular_user"
                comments.append(comment)
        
        def side_effect(*args, **kwargs):
            call_count = getattr(side_effect, 'call_count', 0)
            side_effect.call_count = call_count + 1
            if call_count == 0:
                return mock_issues
            else:
                return comments
        
        mock_session_fixture["filter"].all.side_effect = side_effect
    elif func in [get_open_issues, get_closed_issues]:
        # For regular issue functions, handle comments separately
        def side_effect(*args, **kwargs):
            call_count = getattr(side_effect, 'call_count', 0)
            side_effect.call_count = call_count + 1
            if call_count == 0:
                return mock_issues
            else:
                return [] 
        
        mock_session_fixture["filter"].all.side_effect = side_effect
    else:
        mock_session_fixture["filter"].all.return_value = mock_issues
    
    # Call the function and verify results
    result = func(mock_session_fixture["session"], time_param, repo_name)
    if is_bot and not (func == get_stale_issues and test_case == "Stale Issues Test"):
        assert result == [], f"Bot user '{username}' should be filtered out in {test_case}"
    else:
        if func == get_active_issues and result:
            if isinstance(result, list) and len(result) > 1:
                comment_counts = [issue.get("num_comments_this_week", 0) for issue in result]
                assert comment_counts == sorted(comment_counts, reverse=True), "Active issues not sorted correctly"

        if func == get_stale_issues:
            assert isinstance(result, list), "Stale issues should return a list"
            if result:
                assert "title" in result[0], "Stale issue missing title field"
                assert "time_open" in result[0], "Stale issue missing time_open field"
        
        assert result == expected_result, f"Failed test case {test_case} for function {func.__name__}"


##### PR TESTS #####
@pytest.mark.parametrize("func, repo_name, time_param, pr_state, expected_prs, expected_result, username, bot_status, test_case", [
    # T1: Open PRs, less than one week ago, bot user
    # Expected empty array
    (get_open_prs, "owner/repo", "one_week_ago", 'open', 1, [], "github-bot", "Bot", "T1"),
    
    # T2: Open PRs, less than one week ago, no bot
    (get_open_prs, "owner/repo", "one_week_ago", 'open', 1, [{"title": "Open PR 1", "body": "Description", "url": "http://open_pr1.url", "merged": False, "commits": []}], "developer", "No Bot", "T2"),
    
    # T3: Open PRs, more than one week ago, bot user
    # Expected empty array
    (get_open_prs, "owner/repo", "thirty_days_ago", 'open', 1, [],"dependabot[bot]", "Bot", "T3"),
    
    # T4: Open PRs, more than one week ago, no bot
    # Expected empty array
    (get_open_prs, "owner/repo", "thirty_days_ago", 'open', 1, [],"developer", "No Bot", "T4"),
    
    # T5: Closed PRs, less than one week ago, bot user
    # Expected empty array
    (get_closed_prs, "owner/repo", "one_week_ago", 'closed', 1, [], "renovate-bot", "Bot", "T5"),
    
    # T6: Closed PRs, less than one week ago, no bot
    (get_closed_prs, "owner/repo", "one_week_ago", 'closed', 1, [{"title": "Closed PR 1", "body": "Description", "url": "http://closed_pr1.url", "merged": True, "commits": []}], "developer", "No Bot", "T6"),
    
    # T7: Closed PRs, more than one week ago, bot user
    # Expected empty array
    (get_closed_prs, "owner/repo", "thirty_days_ago", 'closed', 1, [],"ci-bot[bot]", "Bot", "T7"),
    
    # T8: Closed PRs, more than one week ago, no bot
    # Expected empty array
    (get_closed_prs, "owner/repo", "thirty_days_ago", 'closed', 1, [],"developer", "No Bot", "T8"),
    
    # T9: Empty case no PRs
    # Expected empty array
    (get_open_prs, "owner/repo", "one_week_ago", 'open', 0, [], None, "No PR just empty", "T9"),
    
    # Numeric functions tests
    # Function just returns the length
    (get_num_open_prs, "owner/repo", "one_week_ago", 'open', 3, 3,"developer", "No Bot", "Count Open PRs Test"),
    
     # Function just returns the length
    (get_num_closed_prs, "owner/repo", "one_week_ago", 'closed', 2, 2,"developer", "No Bot", "Count Closed PRs Test"),
])
def test_pr_functions(mock_session_fixture, mocker, func, repo_name, time_param, pr_state, 
                      expected_prs, expected_result, username, bot_status, test_case):
    one_week_ago = datetime.now() - timedelta(days=7)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    actual_time_param = one_week_ago if time_param == "one_week_ago" else thirty_days_ago

    if func in [get_num_open_prs, get_num_closed_prs]:
        mock_list = [mocker.Mock() for _ in range(expected_result)]
        result = func(mock_list)
        assert result == expected_result
        return

    if expected_prs == 0:
        mock_query = mocker.Mock()
        mock_filter = mocker.Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []
        
        mock_session_fixture["session"].query.return_value = mock_query
        
        result = func(mock_session_fixture["session"], actual_time_param, repo_name)
        assert result == expected_result
        return

    mock_prs = []
    is_bot = username and ("bot" in username.lower() or "[bot]" in username.lower())

    for i in range(expected_prs):
        pr = mocker.Mock()
        pr.repository_full_name = repo_name
        pr.state = pr_state
        pr.user_login = username if username else "regular_user"
        pr.id = i + 1
        
        if test_case in ["T1", "T2", "T5", "T6"]:
            if pr_state == 'open':
                pr.created_at = one_week_ago + timedelta(days=1)
            else:
                pr.closed_at = one_week_ago + timedelta(days=1)
        elif test_case in ["T3", "T4", "T7", "T8"]:
            if pr_state == 'open':
                pr.created_at = one_week_ago - timedelta(days=5)
            else:
                pr.closed_at = one_week_ago - timedelta(days=5)
        
        if isinstance(expected_result, list) and i < len(expected_result):
            if "title" in expected_result[i]:
                pr.title = expected_result[i]["title"]
                pr.body = expected_result[i].get("body", "")
                pr.html_url = expected_result[i].get("url", "")
                pr.merged = expected_result[i].get("merged", False)
        else:
            pr.title = f"Test PR {i+1}"
            pr.body = "Test PR description"
            pr.html_url = f"https://github.com/test-repo/pull/{i+1}"
            pr.merged = False

        mock_prs.append(pr)

    mock_session_fixture["filter"].all.return_value = mock_prs

    mock_commit_query = mocker.Mock()
    mock_commit_query.filter.return_value = []

    mock_session_fixture["session"].query.side_effect = lambda model: (
        mock_session_fixture["query"] if model == PullRequest else mock_commit_query
    )

    result = func(mock_session_fixture["session"], actual_time_param, repo_name)

    if is_bot:
        assert result == [], f"Bot user '{username}' should be filtered out in {test_case}"
    else:
        assert result == expected_result, f"Failed test case {test_case} for function {func.__name__}"


# Test PR functions with commits
def test_pr_with_commits(mock_session_fixture, mocker):
    one_week_ago = datetime.now() - timedelta(days=7)
    repo_name = "owner/repo"
    
    mock_pr = mocker.Mock()
    mock_pr.id = 1
    mock_pr.repository_full_name = repo_name
    mock_pr.state = 'open'
    mock_pr.created_at = one_week_ago + timedelta(days=1)
    mock_pr.user_login = "developer"
    mock_pr.title = "PR with commits"
    mock_pr.body = "PR description"
    mock_pr.html_url = "http://pr-url.com"
    mock_pr.merged = False

    mock_session_fixture["filter"].all.return_value = [mock_pr]

    mock_commits = [
        mocker.Mock(
            pull_request_id=1,
            commit_message="First commit",
            html_url="http://commit1-url.com",
            sha="abc123"
        ),
        mocker.Mock(
            pull_request_id=1,
            commit_message="Second commit",
            html_url="http://commit2-url.com",
            sha="def456"
        )
    ]

    mock_commit_query = mocker.Mock()
    mock_commit_query.filter.return_value = mock_commits

    mock_session_fixture["session"].query.side_effect = lambda model: (
        mock_session_fixture["query"] if model == PullRequest else mock_commit_query
    )

    expected_result = [{
        "title": "PR with commits",
        "body": "PR description",
        "url": "http://pr-url.com",
        "merged": False,
        "commits": [
            {
                "commit_message": "First commit",
                "html_url": "http://commit1-url.com",
                "sha": "abc123"
            },
            {
                "commit_message": "Second commit",
                "html_url": "http://commit2-url.com",
                "sha": "def456"
            }
        ]
    }]

    result = get_open_prs(mock_session_fixture["session"], one_week_ago, repo_name)

    assert result == expected_result, "PR with commits not properly processed"


##### CONTRIBUTOR TESTS #####

# Setup mock fixture that doesn't return a dictionary for these specific tests
@pytest.fixture
def mock_session_fixture_no_dict(mocker):
    mock_session_no_dict = mocker.Mock()
    return mock_session_no_dict

# Helper function for data (contributor function specific)
def create_mock_data(activity_type, meets_threshold, is_bot, recent_timeframe):
    # Set the date based on the timeframe parameter
    date = one_week_ago + timedelta(days=1) if recent_timeframe else thirty_days_ago - timedelta(days=5)
    
    # Set login name based on bot status
    login = "test-bot" if is_bot else "test-user"
    if is_bot:
        login = f"{login}[bot]"
    
    # Set activity counts based on threshold parameter
    if activity_type == "Comments":
        comments_count = 3 if meets_threshold else 1
        return {
            "comments": [MagicMock(user_login=login, created_at=date) for _ in range(comments_count)],
            "issues": [],
            "pulls": [],
            "commits": []
        }
    elif activity_type == "Issues":
        issues_count = 1 if meets_threshold else 0
        return {
            "comments": [],
            "issues": [MagicMock(user_login=login, created_at=date) for _ in range(issues_count)],
            "pulls": [],
            "commits": []
        }
    elif activity_type == "PRs":
        prs_count = 1 if meets_threshold else 0
        return {
            "comments": [],
            "issues": [],
            "pulls": [MagicMock(user_login=login, created_at=date) for _ in range(prs_count)],
            "commits": []
        }
    elif activity_type == "Commits":
        commits_count = 1 if meets_threshold else 0
        return {
            "comments": [],
            "issues": [],
            "pulls": [], 
            "commits": [MagicMock(commit_author_login=login, committer_date=date) for _ in range(commits_count)]
        }
    else:  # Empty
        return {
            "comments": [],
            "issues": [],
            "pulls": [],
            "commits": []
        }

@pytest.mark.parametrize("activity_type, meets_threshold, is_bot, recent_timeframe, expected_count, test_case", [
    ("Comments", True, True, True, 0, "T1"),     # T1: Comments, Meets, Bot, Less than one week
    ("Comments", True, False, True, 1, "T2"),    # T2: Comments, Meets, No Bot, Less than one week
    ("Comments", False, True, False, 0, "T3"),   # T3: Comments, Does not meet, Bot, More than one week
    ("Comments", False, False, False, 0, "T4"),  # T4: Comments, Does not meet, No Bot, More than one week
    
    ("Issues", True, True, True, 0, "T5"),       # T5: Issues, Meets, Bot, Less than one week
    ("Issues", True, False, True, 1, "T6"),      # T6: Issues, Meets, No Bot, Less than one week
    ("Issues", False, True, False, 0, "T7"),     # T7: Issues, Does not meet, Bot, More than one week
    ("Issues", False, False, False, 0, "T8"),    # T8: Issues, Does not meet, No Bot, More than one week
    
    ("PRs", True, True, True, 0, "T9"),          # T9: PRs, Meets, Bot, Less than one week
    ("PRs", True, False, True, 1, "T10"),        # T10: PRs, Meets, No Bot, Less than one week
    ("PRs", False, True, False, 0, "T11"),       # T11: PRs, Does not meet, Bot, More than one week
    ("PRs", False, False, False, 0, "T12"),      # T12: PRs, Does not meet, No Bot, More than one week
    
    ("Commits", True, True, True, 0, "T13"),     # T13: Commits, Meets, Bot, Less than one week
    ("Commits", True, False, True, 1, "T14"),    # T14: Commits, Meets, No Bot, Less than one week
    ("Commits", False, True, False, 0, "T15"),   # T15: Commits, Does not meet, Bot, More than one week
    ("Commits", False, False, False, 0, "T16"),  # T16: Commits, Does not meet, No Bot, More than one week
    
    ("Empty", False, False, False, 0, "T17"),    # T17: Empty case
])
def test_get_active_contributors(mock_session_fixture_no_dict, activity_type, meets_threshold, 
                               is_bot, recent_timeframe, expected_count, test_case, mocker):
    """
    Test the get_active_contributors function with different combinations
    """
    # Create mock data
    mock_data = create_mock_data(activity_type, meets_threshold, is_bot, recent_timeframe)
    session = mock_session_fixture_no_dict
    
    # Create mock query objects
    mock_commits_query = mocker.Mock()
    mock_pulls_query = mocker.Mock()
    mock_pr_comments_query = mocker.Mock()
    mock_issues_query = mocker.Mock()
    mock_issue_comments_query = mocker.Mock()
    
    # Create filtered mock objects
    mock_commits_filtered = mocker.Mock()
    mock_pulls_filtered = mocker.Mock()
    mock_issues_filtered = mocker.Mock()
    mock_issue_comments_filtered = mocker.Mock()
    
    # Configure .all()
    mock_commits_filtered.all.return_value = mock_data["commits"]
    mock_pulls_filtered.all.return_value = mock_data["pulls"]
    mock_issues_filtered.all.return_value = mock_data["issues"]
    mock_issue_comments_filtered.all.return_value = mock_data["comments"] if activity_type == "Comments" else []
    
    # Configure filter methods
    mock_commits_query.filter.return_value = mock_commits_filtered
    mock_pulls_query.filter.return_value = mock_pulls_filtered
    mock_issues_query.filter.return_value = mock_issues_filtered
    mock_issue_comments_query.filter.return_value = mock_issue_comments_filtered
    pr_comments_iterable = mock_data["comments"] if activity_type == "Comments" else []
    mock_pr_comments_query.filter.return_value = pr_comments_iterable
    
    # Configure session query method
    def mock_query_side_effect(entity):
        if entity == Commit:
            return mock_commits_query
        elif entity == PullRequest:
            return mock_pulls_query
        elif entity == PullRequestComment:
            return mock_pr_comments_query
        elif entity == Issue:
            return mock_issues_query
        elif entity == IssueComment:
            return mock_issue_comments_query
    
    session.query.side_effect = mock_query_side_effect
    
    # function under test
    repo_name = "test/repository"
    
    result = get_active_contributors(session, thirty_days_ago, repo_name)
    actual_count = result[-1]["number_of_active_contributors"] if result else 0
    
    # Assert expected number of active contributors
    assert actual_count == expected_count, f"Failed test case {test_case}: Expected {expected_count} active contributors, got {actual_count}"

    if expected_count > 0:
        contributor = result[0]
        
        if activity_type == "Comments":
            assert contributor["comments"] > 0, f"Failed test case {test_case}: Expected comments > 0"
        elif activity_type == "Issues":
            assert contributor["issues"] > 0, f"Failed test case {test_case}: Expected issues > 0"
        elif activity_type == "PRs":
            assert contributor["pull_requests"] > 0, f"Failed test case {test_case}: Expected pull_requests > 0"
        elif activity_type == "Commits":
            assert contributor["commits"] > 0, f"Failed test case {test_case}: Expected commits > 0"