# Shared utility functions for the newsletter pipeline
# This module contains common functions used across multiple scripts

import requests
import logging

# Checks if a given repo URL is valid, public, and accessible.
# Args: url (str): The GitHub repository URL to check
# Returns:bool: True if repo is accessible and public, False otherwise
def check_repo(url):
    if not url or not isinstance(url, str):
        print(f"Invalid URL format: {url}")
        logging.warning(f"Invalid URL format: {url}")
        return False

    if ".com" not in url:
        print(f"Error: {url} does not contain a valid link.")
        logging.warning(f"URL does not contain .com: {url}")
        return False
    
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.status_code == 404:
            print(f"Error 404: {url} not found or is private.")
            logging.warning(f"Repository not found or private: {url}")
            return False
        # 2xx and 3xx status codes indicate success
        elif 200 <= response.status_code < 400:
            print(f"{url} is accessible and public. Status code: {response.status_code}")
            return True
        else:
            # Other status codes (e.g., 403 Forbidden, 500 Server Error) mean repo is not accessible
            print(f"Repository not accessible: {url} (Status code: {response.status_code})")
            logging.warning(f"Repository returned unexpected status {response.status_code}: {url}")
            return False
            
    except requests.Timeout:
        print(f"Timeout accessing {url}")
        logging.error(f"Timeout accessing repository: {url}")
        return False
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
        logging.error(f"Error accessing repository {url}: {e}")
        return False

# Extracts the repository name (owner/repo) from a GitHub URL.
# Args: url (str): The GitHub repository URL
# Returns: str: The repository name in format 'owner/repo', or None if invalid
def get_repo_name(url):
    if not url:
        return None
    
    parts = url.split('/')
    if len(parts) >= 5 and parts[2] == 'github.com':
        return f"{parts[3]}/{parts[4]}"
    return None
