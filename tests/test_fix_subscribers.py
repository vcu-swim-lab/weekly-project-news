import pytest
import json
import re
import requests
from unittest.mock import patch, mock_open, MagicMock, call
import io
import sys
import os

# Import the functions from the file to test
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import fix_subscribers_file


@pytest.mark.parametrize(
    "test_id, url_is_valid, repo_is_public, json_is_valid, expected_outcome",
    [
        # T1: All conditions are True
        ("T1", True, True, True, "retained"),

        # T2: Valid URL, Public Repo, Invalid JSON
        ("T2", True, True, False, "removed"),

        # T3: Valid URL, Private Repo, Valid JSON
        ("T3", True, False, True, "removed"),

        # T4: Valid URL, Private Repo, Invalid JSON
        ("T4", True, False, False, "removed"),

        # T5: Invalid URL, Public Repo, Valid JSON
        ("T5", False, True, True, "removed"),

        # T6: Invalid URL, Public Repo, Invalid JSON
        ("T6", False, True, False, "removed"),

        # T7: Invalid URL, Private Repo, Valid JSON
        ("T7", False, False, True, "removed"),

        # T8: All conditions are False
        ("T8", False, False, False, "removed"),
    ]
)
def test_process_and_check_repo(mocker, test_id, url_is_valid, repo_is_public, json_is_valid, expected_outcome):
    # Setup test data based on parameters
    test_repo = "user/repo" if json_is_valid else "invalid-format"
    repo_url = f"https://github.com/{test_repo}" if url_is_valid else "not-a-url"
    
    test_data = {
        "count": 1,
        "results": [
            {
                "id": "test-id",
                "creation_date": "2025-03-26T13:58:54.122818Z",
                "notes": "",
                "metadata": {
                    "repo_name": repo_url
                },
                "tags": [],
                "referrer_url": "https://test.com",
                "secondary_id": 38,
                "source": "api",
                "email": "test@example.com",
                "subscriber_type": "regular"
            }
        ]
    }
    
    test_json_str = json.dumps(test_data)
    
    # Mock the file operations
    m = mock_open(read_data=test_json_str)
    mocker.patch('builtins.open', m)
    
    # Mock the regex search for repo name format and patch
    if json_is_valid:
        original_re_search = re.search
        def mock_re_search(pattern, string, *args, **kwargs):
            if pattern == r'(?:github\.com/)?([^/]+/[^/]+)/?$':
                if string == repo_url and json_is_valid:
                    match = MagicMock()
                    match.group.return_value = test_repo
                    return match
                else:
                    return None
            return original_re_search(pattern, string, *args, **kwargs)
        mocker.patch('re.search', side_effect=mock_re_search)
    else:
        mocker.patch('re.search', return_value=None)
    
    mock_response = MagicMock()
    mock_response.status_code = 200 if repo_is_public else 404
    
    def mock_requests_head(url, **kwargs):
        if not url_is_valid:
            raise requests.RequestException("Connection error")
        return mock_response
    
    mocker.patch('requests.head', side_effect=mock_requests_head)
    mocker.patch('builtins.print')
    
    with pytest.raises(Exception) if not url_is_valid and not json_is_valid else patch('fix_subscribers_file.main'):
        try:
            fix_subscribers_file.main()
        except Exception as e:
            if not url_is_valid and not json_is_valid:
                raise e
            else:
                pytest.fail(f"Unexpected exception: {e}")
    
    # Test process_repo_names
    processed_data = fix_subscribers_file.process_repo_names(test_data.copy())
    
    # Test check_repo
    repo_check_result = fix_subscribers_file.check_repo(repo_url)
    expected_repo_check = True if not (url_is_valid and repo_is_public) else None
    assert repo_check_result == expected_repo_check, f"Test {test_id}: check_repo returned {repo_check_result}, expected {expected_repo_check}"
    
    # Test delete_problem_repos
    if json_is_valid:
        test_data_copy = processed_data.copy()
        fix_subscribers_file.delete_problem_repos(test_data_copy)
        
        expected_count = 0 if expected_outcome == "removed" else 1
        assert len(test_data_copy["results"]) == expected_count, f"Test {test_id}: Expected {expected_count} results after delete_problem_repos"