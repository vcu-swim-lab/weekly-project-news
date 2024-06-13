import pytest
from datetime import datetime, timedelta, timezone
from acquire_project_data import get_open_issues

one_week_ago = datetime.now(timezone.utc) - timedelta(weeks=1)

# Consider adding code to print out output of mock issues
# Consider adding everything to issues (i.e. ID, comments, labels, created_at, etc.)
# CONTAINS 7 MOCK OPEN ISSUES
@pytest.fixture
def mock_issues(mocker):
    # List to contain mock issues
    mock_issue_list = []
    
    # OPEN ISSUE 1: LABELS AND COMMENTS
    mock_issue1 = mocker.Mock()
    mock_issue1.state = 'open'
    mock_issue1.pull_request = False
    mock_issue1.user.login = "user1"
    label1 = mocker.Mock()
    label1.name = 'label1'
    mock_issue1.get_labels.return_value = [label1]
    # OPEN ISSUE 1 COMMENTS
    mock_comment1 = mocker.Mock()
    mock_comment1.user.login = "commenter1"
    mock_comment1.body = "This is a comment"
    mock_issue1.get_comments.return_value = [mock_comment1]
    mock_issue_list.append(mock_issue1) # Add to mock issues list
    
    
    
    # OPEN ISSUE 2: LABELS NO COMMENTS
    mock_issue2 = mocker.Mock()
    mock_issue2.state = 'open'
    mock_issue2.pull_request = False
    mock_issue2.user.login = "user2"
    label2 = mocker.Mock()
    label2.name = 'label2'
    mock_issue2.get_labels.return_value = [label2]
    mock_issue2.get_comments.return_value = []
    mock_issue_list.append(mock_issue2) # Add to mock issues list
    
    
    
    # OPEN ISSUE 3: PULL REQUEST NO COMMENTS
    mock_issue3 = mocker.Mock()
    mock_issue3.state = 'open'
    mock_issue3.pull_request = True
    mock_issue3.user.login = "user3"
    label3 = mocker.Mock()
    label3.name = 'label3'
    mock_issue3.get_labels.return_value = [label3]
    mock_issue3.get_comments.return_value = []
    mock_issue_list.append(mock_issue3) # Add to mock issues list
    
    
    
    # OPEN ISSUE 4: '[bot]' IN ISSUE USER
    mock_issue4 = mocker.Mock()
    mock_issue4.state = 'open'
    mock_issue4.pull_request = False
    mock_issue4.user.login = 'test4[bot]'
    mock_issue4.get_labels.return_value = []
    mock_issue4.get_comments.return_value = []
    mock_issue_list.append(mock_issue4) # Add to mock issues list
    
    
    # OPEN ISSUE 5: 'bot' IN ISSUE USER
    mock_issue5 = mocker.Mock()
    mock_issue5.state = 'open'
    mock_issue5.pull_request = False
    mock_issue5.user.login = 'test5bot'
    mock_issue5.get_labels.return_value = []
    mock_issue5.get_comments.return_value = []
    mock_issue_list.append(mock_issue5) # Add to mock issues list
    
    
    # OPEN ISSUE 6: '[bot]' IN COMMENT USER
    mock_issue6 = mocker.Mock()
    mock_issue6.state = 'open'
    mock_issue6.pull_request = False
    mock_issue6.user.login = "user6"
    mock_issue6.get_labels.return_value = []
    # OPEN ISSUE 6 COMMENTS
    mock_comment6 = mocker.Mock()
    mock_comment6.user.login = 'comment6[bot]'
    mock_comment6.body = "This is a comment"
    mock_issue6.get_comments.return_value = [mock_comment6]
    mock_issue_list.append(mock_issue6) # Add to mock issues list
    
    
    
    # OPEN ISSUE 7: 'bot' IN COMMENT USER
    mock_issue7 = mocker.Mock()
    mock_issue7.state = "open"
    mock_issue7.pull_request = False
    mock_issue7.user.login = "user7"
    mock_issue7.get_labels.return_value = []
    # OPEN ISSUE 7 COMMENTS
    mock_comment7 = mocker.Mock()
    mock_comment7.user.login = "comment7bot"
    mock_comment7.body = "This is a comment"
    mock_issue7.get_comments.return_value = [mock_comment7]
    mock_issue_list.append(mock_issue7) # Add to mock issues list
    
    return mock_issue_list

@pytest.fixture
def mock_pull_requests(mocker):
    mock_pull_request_list = []
    return mock_pull_request_list
    
def mock_commits(mocker):
    mock_commit_list = []
    return mock_commit_list

@pytest.fixture
def mock_repo(mocker, mock_issues, mock_pull_requests, mock_commits):
    mock_repo = mocker.Mock()
    mock_repo.get_issues.return_value = mock_issues
    mock_repo.get_pulls.return_value = mock_pull_requests
    mock_repo.get_commits.return_value = mock_commits
    return mock_repo

@pytest.fixture
def g(mocker, mock_repo):
    g = mocker.Mock()
    g.get_repo.return_value = mock_repo
    return g



# OPEN ISSUE TEST 1: Issue has comments and labels
# Input: 
# Expected Output:
def test_get_open_issues_1_labels_and_comments(mocker, g, mock_repo, mock_open_issues):
    mocker.patch('acquire_project_data.rate_limit_check')
    
    open_issues = get_open_issues(g, mock_repo, one_week_ago)
    open_issues = [issue for issue in mock_issues if not issue["closed"]]

    # Make sure no closed issues get added

    # Test for user, label, commenter, and comments
    assert open_issues[0]["user"] == "user1"
    assert open_issues[0]["labels"] == ["label1"]
    assert open_issues[0]["comments"][0]["user"] == "commenter1"
    assert open_issues[0]["comments"][0]["body"] == "This is a comment"

# OPEN ISSUE TEST 2: Issue has labels but no comments
# Input: 
# Expected Output:
def test_get_open_issues_2_no_comments(mocker, g, mock_repo, mock_issues):
    mocker.patch('acquire_project_data.rate_limit_check')
  
    open_issues = get_open_issues(g, mock_repo, one_week_ago)
    open_issues = [issue for issue in mock_issues if not issue["closed"]]
    
    # Test that the user is correct, the label is correct, and there are no comments
    assert open_issues[1]["user"] == "user2"
    assert open_issues[1]["labels"] == ["label2"]
    assert open_issues[1]["comments"] == []
    

# OPEN ISSUE TEST 3: Issue is a pull request with labels but no comments.
# Input:
# Expected Output: 
def test_get_open_issues_3_pull_request(mocker, g, mock_repo, mock_issues):
    mocker.patch('acquire_project_data.rate_limit_check')

    open_issues = get_open_issues(g, mock_repo, one_week_ago)
    open_issues = [issue for issue in mock_issues if not issue["closed"]]

    # Assert that the number of open issues remains the same
    for issue in open_issues:
        assert issue['pull_request'] == False
   
    
def test_get_open_issues_4_bot(mocker, g, mock_repo, mock_issues):
    mocker.patch('acquire_project_data.rate_limit_check')
    
    open_issues = get_open_issues(g, mock_repo, one_week_ago)
    open_issues = [issue for issue in mock_issues if not issue["closed"]]
    
    assert open_issues[3]["user"]
    
    
    
    