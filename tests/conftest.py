import os
import sys

# parse_github_data.py reads GITHUB_API_KEYS at import time, so set it here
# (conftest.py is loaded before any test module).
os.environ.setdefault("GITHUB_API_KEYS", "testkey1 testkey2 testkey3")
os.environ.setdefault("BUTTONDOWN_API_KEY", "test-buttondown-key")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
