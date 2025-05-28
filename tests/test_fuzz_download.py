# This file contains the tests that are run to fuzz the download_new_subscribers.py file
# It fuzzes random strings and status codes
# The fuzzes are run 100 times, but can be changed if needed
# Run with pytest

import pytest
import responses
import os
import json
from unittest.mock import patch, mock_open
import sys
import random
import string
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from download_new_subscribers import download_subscribers

# Fuzz string for URLs 
def generate_random_string(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Fuzz different status codes 
def generate_random_status_code():
    status_codes = [200, 201, 400, 401, 403, 404, 429, 500, 502, 503]
    return random.choice(status_codes)

@responses.activate
def test_fuzzing_api_key():
    for _ in range(100):
        # Fuzz a bunch of API keys
        key_type = random.randint(0, 3)
        print(f"Testing key: {key_type}")
        if key_type == 0:
            api_key = ""
        elif key_type == 1:
            api_key = generate_random_string(random.randint(1, 10))  # Short key
        elif key_type == 2:
            api_key = generate_random_string(random.randint(100, 500))  # Very long key
        else:
            api_key = None
        
        status_code = generate_random_status_code()
        mock_data = {"results": [{"email": "test@example.com"}]} if status_code == 200 else {}
        
        responses.reset()
        responses.add(
            responses.GET,
            "https://api.buttondown.email/v1/subscribers",
            json=mock_data,
            status=status_code
        )

        # Run test with patched environment
        with patch("dotenv.load_dotenv"):
            with patch("builtins.open", mock_open()) as mock_file:
                try:
                    success, response = download_subscribers(api_key=api_key)
                    assert isinstance(success, bool)
                    assert response is not None
                except Exception as e:
                    pytest.fail(f"Fuzzing test failed with api_key={api_key}, error: {str(e)}")

@responses.activate
def test_fuzzing_response_content():
    for _ in range(100):
        api_key = "valid_api_key"

        # Test different response types
        response_type = random.randint(0, 3)
        print(f"Testing response type: {response_type}")
        if response_type == 0:
            mock_data = {"results": []}
        elif response_type == 1:
            mock_data = {"results": [{"email": generate_random_string(10)} for _ in range(100)]}
        elif response_type == 2:
            mock_data = {"some_unexpected_field": generate_random_string(50)}
        else:
            mock_data = {}
        
        status_code = generate_random_status_code()
        responses.reset()
        responses.add(
            responses.GET,
            "https://api.buttondown.email/v1/subscribers",
            json=mock_data,
            status=status_code
        )
        
        # Run test with patched environment
        with patch("dotenv.load_dotenv"):
            with patch.dict(os.environ, {"BUTTONDOWN_API_KEY": api_key}):
                with patch("builtins.open", mock_open()) as mock_file:
                    try:
                        success, response = download_subscribers(api_key=None)
                        # Basic validation - just checking it doesn't crash
                        assert isinstance(success, bool)
                    except Exception as e:
                        pytest.fail(f"Fuzzing test failed with response={mock_data}, error: {str(e)}")