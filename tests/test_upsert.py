# Tests for the update_db upsert: issues/PRs that are active this week but not
# yet in the DB must be INSERTED (backfilled) rather than logged as "does not
# exist", while items already present are still UPDATED.

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import parse_github_data
import update_db
from tables.base import Base
from tables.issue import Issue
from tables.pull_request import PullRequest

REPO = "owner/repo"


def _issue(id, number, state, is_pr=False, **extra):
    kind = "pull" if is_pr else "issues"
    d = {
        'id': id,
        'number': number,
        'state': state,
        'title': f'item {id}',
        'body': '',
        'comments': 0,
        'closed_at': None,
        'created_at': '2026-07-11T00:00:00+00:00',
        'updated_at': '2026-07-12T00:00:00+00:00',
        'html_url': f'https://github.com/{REPO}/{kind}/{number}',
        'user': {'login': 'alice'},
    }
    if is_pr:
        d['pull_request'] = {'merged_at': None}
    d.update(extra)
    return d


@pytest.fixture
def session(monkeypatch):
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()

    # The reused insert_* helpers operate on parse_github_data.session.
    saved = getattr(parse_github_data, 'session', None)
    parse_github_data.session = s

    # Stub every network call the loop makes.
    monkeypatch.setattr(update_db, 'get_issue_comments', lambda *a, **k: [])
    monkeypatch.setattr(update_db, 'get_pr_comments', lambda *a, **k: [])
    monkeypatch.setattr(update_db, 'get_pr_commits', lambda *a, **k: [])
    monkeypatch.setattr(update_db, 'get_issue_labels', lambda *a, **k: [])
    monkeypatch.setattr(update_db, 'get_latest_release', lambda *a, **k: None)
    monkeypatch.setattr(update_db, 'rate_limit_check', lambda *a, **k: None)

    yield s

    s.close()
    if saved is not None:
        parse_github_data.session = saved


def test_missing_issue_is_inserted(session, monkeypatch):
    monkeypatch.setattr(update_db, 'get_issues', lambda *a, **k: [_issue(2, 2, 'open')])

    update_db.update_all_data(session, REPO, None)

    row = session.query(Issue).filter_by(id=2).first()
    assert row is not None
    assert row.state == 'open'
    assert row.repository_full_name == REPO


def test_missing_pull_request_is_inserted(session, monkeypatch):
    monkeypatch.setattr(update_db, 'get_issues', lambda *a, **k: [_issue(3, 3, 'open', is_pr=True)])

    update_db.update_all_data(session, REPO, None)

    row = session.query(PullRequest).filter_by(id=3).first()
    assert row is not None
    assert row.state == 'open'


def test_existing_issue_is_updated_not_reinserted(session, monkeypatch):
    # Seed an existing issue in the "open" state.
    session.add(Issue(id=1, number=1, state='open', title='item 1',
                      repository_full_name=REPO, comments=0))
    session.commit()

    # GitHub now reports it as closed.
    monkeypatch.setattr(update_db, 'get_issues', lambda *a, **k: [_issue(1, 1, 'closed')])

    update_db.update_all_data(session, REPO, None)

    rows = session.query(Issue).filter_by(id=1).all()
    assert len(rows) == 1          # updated in place, not duplicated
    assert rows[0].state == 'closed'


def test_mixed_batch_inserts_and_updates(session, monkeypatch):
    session.add(Issue(id=1, number=1, state='open', title='item 1',
                      repository_full_name=REPO, comments=0))
    session.commit()

    monkeypatch.setattr(update_db, 'get_issues', lambda *a, **k: [
        _issue(1, 1, 'closed'),            # existing -> update
        _issue(2, 2, 'open'),              # new issue -> insert
        _issue(3, 3, 'open', is_pr=True),  # new PR -> insert
    ])

    update_db.update_all_data(session, REPO, None)

    assert session.query(Issue).filter_by(id=1).first().state == 'closed'
    assert session.query(Issue).filter_by(id=2).first() is not None
    assert session.query(PullRequest).filter_by(id=3).first() is not None
