from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import pytest
from tables.base import Base, engine
from tables.repository import Repository
from tables.issue import Issue, IssueComment
from tables.pull_request import PullRequest, PullRequestComment
from tables.commit import Commit
from tables.user import User
from datetime import datetime, timedelta, timezone
from parse_github_data import *

Base = declarative_base()
engine = create_engine('sqlite:///test.db')

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="module")
def valid_issue():
    valid_issue = Issue(
            id = 1,
            html_url='https://github.com/issue1',
            number = 1,
            state = 'open',
            title = 'Issue 1',
            body = 'test open issue',
            comments = 2,
            created_at = datetime.now() - timedelta(days=3),
            closed_at = None,
            updated_at = datetime.now() - timedelta(days=3),
            user_login = 'user1',
            repository_full_name = 'repo1'
        )
    
    return valid_issue

# TODO Test for 'bot'

# TODO Test for '[bot]'

# Contains all test cases
class TestDB:      
    def test_insert_valid_issue(self, db_session, valid_issue):
        insert_issue(valid_issue)
        
        issue = db_session.query(Issue).filter_by(id = 1).first()
        
        assert issue.id == 1
        assert issue.html_url == 'https://github.com/issue1'
        assert issue.number == 1
        assert issue.state == 'open'
        assert issue.title == 'Issue 1'
        assert issue.body == 'test open issue'
        assert issue.comments == 2
        assert issue.created_at == datetime.now() - timedelta(days=3)
        assert issue.closed_at == None
        assert issue.updated_at == datetime.now() - timedelta(days=3)
        assert issue.user_login == 'user1'
        assert issue.repository_full_name == 'repo1'
    
    @pytest.mark.xfail(raises=IntegrityError)
    def test_bot_issue(self, db_session):
        print()
        