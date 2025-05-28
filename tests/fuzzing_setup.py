# This is a helper file to set up the functions for fuzzing such as generating strings

import random
import string
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Class for setting up the fuzz
class FuzzingSetup:
    
    @staticmethod
    def create_mock_session():
        mock_filter = MagicMock()
        mock_query = MagicMock()
        mock_session = MagicMock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        
        return {
            "session": mock_session,
            "query": mock_query,
            "filter": mock_filter
        }
    
    @staticmethod
    def generate_random_string(min_length=1, max_length=100):
        length = random.randint(min_length, max_length)
        chars = string.ascii_letters + string.digits + string.punctuation + ' '
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def generate_random_repo_name():
        choice = random.randint(0, 5)
        
        if choice == 0:
            # Standard format: owner/repo
            owner = FuzzingSetup.generate_random_string(3, 20)
            repo = FuzzingSetup.generate_random_string(3, 20)
            return f"{owner}/{repo}"
        elif choice == 1:
            # Very long name
            owner = FuzzingSetup.generate_random_string(50, 150)
            repo = FuzzingSetup.generate_random_string(50, 150)
            return f"{owner}/{repo}"
        elif choice == 2:
            # Invalid format (no slash)
            return FuzzingSetup.generate_random_string(5, 30)
        elif choice == 3:
            # Multiple slashes
            parts = [FuzzingSetup.generate_random_string(3, 10) for _ in range(random.randint(3, 5))]
            return '/'.join(parts)
        elif choice == 4:
            # Empty string
            return ""
        else:
            # None value
            return None
    
    @staticmethod
    def generate_random_version():
        """Generate a random version string."""
        choice = random.randint(0, 4)
        
        if choice == 0:
            # Standard
            major = random.randint(0, 20)
            minor = random.randint(0, 99)
            patch = random.randint(0, 999)
            prefix = random.choice(["v", ""])
            return f"{prefix}{major}.{minor}.{patch}"
        elif choice == 1:
            # Alpha/beta/rc version
            major = random.randint(0, 10)
            minor = random.randint(0, 99)
            suffix = random.choice(["-alpha", "-beta", "-rc", ".alpha", ".beta"])
            suffix_num = random.randint(1, 10)
            return f"v{major}.{minor}{suffix}.{suffix_num}"
        elif choice == 2:
            # Invalid version
            return FuzzingSetup.generate_random_string(1, 20)
        elif choice == 3:
            # Empty string
            return ""
        else:
            # None value
            return None
    
    @staticmethod
    def generate_random_date():
        choice = random.randint(0, 5)
        
        # Random datetime
        days = random.randint(-1000, 1000)
        hours = random.randint(0, 23)
        minutes = random.randint(0, 59)
        seconds = random.randint(0, 59)
        
        date_obj = datetime.now() + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        
        if choice == 0:
            # ISOformat
            return date_obj.isoformat()
        elif choice == 1:
            # DateTime object
            class MockDateTime:
                def __init__(self, dt):
                    self.dt = dt
                
                def isoformat(self):
                    return self.dt.isoformat()
            
            return MockDateTime(date_obj)
        elif choice == 2:
            # Invalid date format
            return FuzzingSetup.generate_random_string(5, 25)
        elif choice == 3:
            # Empty string
            return ""
        elif choice == 4:
            # None value
            return None
        else:
            # Random string that looks like a date
            return f"{random.randint(1900, 2100)}-{random.randint(1, 12)}-{random.randint(1, 28)}"
    
    @staticmethod
    def generate_random_description():
        choice = random.randint(0, 4)
        
        if choice == 0:
            # Normal description
            return FuzzingSetup.generate_random_string(10, 200)
        elif choice == 1:
            # Very long description
            return FuzzingSetup.generate_random_string(1000, 3000)
        elif choice == 2:
            # Description with special characters
            return FuzzingSetup.generate_random_string(10, 100) + "\n\n" + FuzzingSetup.generate_random_string(10, 100)
        elif choice == 3:
            # Empty string
            return ""
        else:
            # None
            return None

@staticmethod
def create_mock_date_object(date_obj=None):
    if date_obj is None:
        days = random.randint(-1000, 1000)
        date_obj = datetime.now() + timedelta(days=days)
    
    class MockDateTime:
        def isoformat(self):
            return date_obj.isoformat()
    
    return MockDateTime()

@staticmethod
def generate_data_for_function(func_name):
    if func_name == "get_latest_release":
        return FuzzingSetup.generate_random_version()
    elif func_name == "get_release_description":
        return FuzzingSetup.generate_random_description()
    elif func_name == "get_release_create_date":
        choice = random.randint(0, 3)
        if choice == 0:
            return FuzzingSetup.create_mock_date_object()
        elif choice == 1:
            return FuzzingSetup.generate_random_date()
        elif choice == 2:
            return ""
        else:
            return None
    else:
        return None