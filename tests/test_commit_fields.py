# Tests for fix #5: extract_commit_core_fields replaces the `X if not None
# else ''` no-op guards, which did nothing and could raise when GitHub returned
# a null `author` for a commit.

from datetime import datetime

import parse_github_data


def test_normal_commit():
    commit = {
        'author': {'login': 'octocat'},
        'commit': {
            'committer': {'date': '2024-01-02T03:04:05'},
            'message': 'Fix bug',
        },
    }
    fields = parse_github_data.extract_commit_core_fields(commit)
    assert fields['commit_author_login'] == 'octocat'
    assert fields['committer_date'] == datetime(2024, 1, 2, 3, 4, 5)
    assert fields['commit_message'] == 'Fix bug'


def test_null_author_does_not_raise():
    # GitHub returns author: null for commits not linked to a GitHub account.
    # The old code did commit['author']['login'] -> TypeError.
    commit = {
        'author': None,
        'commit': {'committer': {'date': '2024-01-02T03:04:05'}, 'message': 'x'},
    }
    fields = parse_github_data.extract_commit_core_fields(commit)
    assert fields['commit_author_login'] == ''


def test_missing_committer_date_is_none():
    commit = {'author': {'login': 'a'}, 'commit': {'committer': {}, 'message': 'm'}}
    fields = parse_github_data.extract_commit_core_fields(commit)
    assert fields['committer_date'] is None


def test_empty_payload_returns_safe_defaults():
    fields = parse_github_data.extract_commit_core_fields({})
    assert fields == {
        'commit_author_login': '',
        'committer_date': None,
        'commit_message': '',
    }
