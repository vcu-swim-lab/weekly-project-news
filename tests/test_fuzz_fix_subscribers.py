import pytest
import random
import string
import json
from unittest.mock import patch, mock_open, MagicMock
import re
import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import fix_subscribers_file


# Generate random strings for URLs
def generate_random_string(length=10):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

# Generate random repo names
def generate_random_repo_name():
    formats = [
        # Fuzz valid inputs for repo name
        # 1: user/repo
        # 2: github.com/user/repo
        # 3: https://github.com/user/repo
        # 4: with trailing slash
        f"{generate_random_string()}/{generate_random_string()}",
        f"github.com/{generate_random_string()}/{generate_random_string()}",
        f"https://github.com/{generate_random_string()}/{generate_random_string()}",
        f"https://github.com/{generate_random_string()}/{generate_random_string()}/",
        
        # Invalid formats for repo name
        # 1: Just a string
        # 2: User w/ trailing slash
        # 3: Slash and repo
        # 4: Wrong repo domain
        # 5: Missing repo part
        # 6: Wrong site
        # 7: Empty string
        generate_random_string(),
        f"{generate_random_string()}/",
        f"/{generate_random_string()}",
        f"https://{generate_random_string()}.com/{generate_random_string()}",
        f"github.com/{generate_random_string()}",
        f"https://gitlab.com/{generate_random_string()}/{generate_random_string()}",
        ""
    ]
    return random.choice(formats)

# Fuzz random subscribers with JSON format
def generate_random_subscriber():
    return {
        "id": generate_random_string(),
        "creation_date": "2025-03-26T13:58:54.122818Z",
        "notes": generate_random_string(20) if random.random() > 0.5 else "",
        "metadata": {
            "repo_name": generate_random_repo_name(),
            **({"extra_field": generate_random_string()} if random.random() > 0.7 else {})
        },
        "tags": [],
        "email": f"{generate_random_string()}@{generate_random_string()}.com",
        "subscriber_type": random.choice(["regular", "paid", "trial"])
    }

# Fuzz with random repo names
def test_process_repo_names_fuzzing():
    num_subscribers = random.randint(1, 100)
    
    test_data = {
        "count": num_subscribers,
        "results": [generate_random_subscriber() for _ in range(num_subscribers)]
    }
    valid_formats = 0
    for subscriber in test_data["results"]:
        repo_name = subscriber["metadata"].get("repo_name", "")
        if repo_name and isinstance(repo_name, str):
            if re.search(r'(?:github\.com/)?([^/]+/[^/]+)/?$', repo_name, re.IGNORECASE):
                valid_formats += 1
    
    # Process the data
    try:
        result = fix_subscribers_file.process_repo_names(test_data)
        
        assert all(
            subscriber["metadata"]["repo_name"].startswith("https://github.com/")
            for subscriber in result["results"]
        )

        assert len(result["results"]) == valid_formats, f"Expected {valid_formats} valid repos, got {len(result['results'])}"
    
    except Exception as e:
        pytest.fail(f"process_repo_names failed with random data: {e}\nTest data: {test_data}")


# Fuzz 100 repo names
def test_check_repo_fuzzing(mocker):
    urls = [generate_random_repo_name() for _ in range(100)]
    
    def mock_head(url, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200 if "valid" in url else 404
        
        if not isinstance(url, str) or "://" not in url:
            raise requests.RequestException("Not a valid URL")
            
        return mock_response
    
    mocker.patch("requests.head", side_effect=mock_head)
    mocker.patch("builtins.print")
    for url in urls:
        try:
            result = fix_subscribers_file.check_repo(url)
            
            # Expected behavior:
            # - URLs with "valid" and proper format should return None (valid)
            # - Others should return True (invalid)
            if url and isinstance(url, str) and "://" in url and ".com" in url and "valid" in url:
                assert result is None, f"Expected valid URL {url} to return None, got {result}"
            else:
                assert result is True, f"Expected invalid URL {url} to return True, got {result}"
                
        except Exception as e:
            pytest.fail(f"check_repo failed with URL '{url}': {e}")

 # Fuzz 50-100 random subscribers
def test_delete_problem_repos_fuzzing(mocker):
    num_subscribers = random.randint(50, 100)
    
    test_data = {
        "count": num_subscribers,
        "results": []
    }
    
    expected_valid = 0
    for _ in range(num_subscribers):
        subscriber = generate_random_subscriber()
        will_pass = random.random() < 0.6
        if will_pass:
            subscriber["metadata"]["repo_name"] = f"https://github.com/valid-{generate_random_string()}/repo"
            expected_valid += 1
        test_data["results"].append(subscriber)
    
    def mock_check_repo(url):
        return None if "valid-" in url else True
    
    mocker.patch("fix_subscribers_file.check_repo", side_effect=mock_check_repo)
    mocker.patch("builtins.print")
    
    # Run the function
    try:
        data_copy = json.loads(json.dumps(test_data))
        fix_subscribers_file.delete_problem_repos(data_copy)
        
        assert len(data_copy["results"]) == expected_valid
        assert all("valid-" in sub["metadata"].get("repo_name", "") for sub in data_copy["results"])

        assert data_copy["count"] == expected_valid
        
    except Exception as e:
        pytest.fail(f"delete_problem_repos failed with fuzzing data: {e}")

# Fuzz 50-100 of subscribers
def test_main_function_fuzzing(mocker):
    num_subscribers = random.randint(50, 100)
    
    # Create test data with some valid and some invalid repos
    test_data = {
        "count": num_subscribers,
        "results": []
    }
    
    valid_count = 0
    for _ in range(num_subscribers):
        subscriber = generate_random_subscriber()
        
        if random.random() < 0.4:
            subscriber["metadata"]["repo_name"] = f"https://github.com/valid-{generate_random_string()}/repo"
            valid_count += 1
            
        test_data["results"].append(subscriber)
    
    m = mock_open(read_data=json.dumps(test_data))
    mocker.patch('builtins.open', m)
    
    def mock_check_repo(url):
        return None if "valid-" in url else True
    
    mocker.patch('fix_subscribers_file.check_repo', side_effect=mock_check_repo)
    mocker.patch('builtins.print')
    
    fix_subscribers_file.main()
    
    assert m().write.called, "File write was not called during main function"
    assert fix_subscribers_file.check_repo.called