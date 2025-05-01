import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sort_data import *
from fuzzing_setup import *

# Map function names to actual functions
function_map = {
    "get_latest_release": get_latest_release,
    "get_release_description": get_release_description,
    "get_release_create_date": get_release_create_date
}

# Parameterized fuzzing test for all release functions
@pytest.mark.parametrize("func_name", [
    "get_latest_release", 
    "get_release_description", 
    "get_release_create_date"
])
def test_release_functions_fuzzing(func_name):
    func = function_map[func_name]
    
    # Number of fuzzing iterations
    iterations = 100
    
    for _ in range(iterations):
        # Create mock session
        mocks = FuzzingSetup.create_mock_session()
        mock_session = mocks["session"]
        
        # Generate random data
        repo_name = FuzzingSetup.generate_random_repo_name()
        if func_name == "get_latest_release":
            mock_value = FuzzingSetup.generate_random_version()
        elif func_name == "get_release_description":
            mock_value = FuzzingSetup.generate_random_description()
        elif func_name == "get_release_create_date":
            choice = random.randint(0, 2)
            if choice == 0:
                days = random.randint(-1000, 1000)
                date_obj = datetime.now() + timedelta(days=days)
                
                class MockDateTime:
                    def isoformat(self):
                        return date_obj.isoformat()
                
                mock_value = MockDateTime()
            else:
                mock_value = random.choice([None, ""])
        
        mocks["filter"].scalar.return_value = mock_value
        
        try:
            # Call the function under test
            result = func(mock_session, repo_name)
            if func_name == "get_latest_release" or func_name == "get_release_description":
                if mock_value is None:
                    assert result is None, f"None input should return None, got {repr(result)}"
            
            elif func_name == "get_release_create_date":
                if mock_value is None:
                    assert result is None, f"None date should return None, got {repr(result)}"
                elif hasattr(mock_value, 'isoformat'):
                    assert result == mock_value.isoformat(), f"Expected {mock_value.isoformat()}, got {repr(result)}"
                
        except AssertionError as e:
            pytest.fail(f"Function {func_name} assertion failed with input: {repo_name}, mock value: {repr(mock_value)}, error: {str(e)}")
        except Exception as e:
            pytest.fail(f"Function {func_name} crashed with input: {repo_name}, mock value: {repr(mock_value)}, error: {str(e)}")