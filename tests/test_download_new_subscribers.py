import pytest
import responses
import os
import json
from unittest.mock import patch, mock_open
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from download_new_subscribers import download_subscribers

@pytest.mark.parametrize("test_id, status_code, api_key_valid, expected_success", [
    ("T1", 200, True, True),     # T1: Valid key, successful response
    ("T2", 200, False, False),   # T2: Invalid key
    ("T3", 401, True, False),    # T3: Valid key but unauthorized response
    ("T4", 401, False, False),   # T4: Invalid key, unauthorized response
    ("T5", 404, True, False),    # T5: Valid key, not found
    ("T6", 404, False, False),   # T6: Invalid key, not found
    ("T7", 500, True, False),    # T7: Valid key, server error
    ("T8", 500, False, False),   # T8: Invalid key, server error
])
@responses.activate
def test_download_subscribers(test_id, status_code, api_key_valid, expected_success):
    mock_data = {"results": [{"email": "test@example.com"}]} if status_code == 200 else {}
    responses.add(
        responses.GET,
        "https://api.buttondown.email/v1/subscribers",
        json=mock_data,
        status=status_code
    )
    api_key = "valid_api_key" if api_key_valid else "invalid_api_key"
    
    with patch("dotenv.load_dotenv"):
        env_mock = {"BUTTONDOWN_API_KEY": api_key} if api_key_valid else {}
        with patch.dict(os.environ, env_mock, clear=True):
            with patch("builtins.open", mock_open()) as mock_file:
                success, response_data = download_subscribers(api_key=None)
    
    assert success == expected_success
    
    if expected_success:
        assert response_data == mock_data
        mock_file.assert_called_with('subscribers.json', 'w')
    else:
        assert "status_code" in response_data
        assert response_data["status_code"] == status_code