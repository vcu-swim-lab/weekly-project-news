# Tests for fix #2: parse_github_data must use repo_utils.check_repo /
# get_repo_name (correct semantics) rather than shadowing them with local
# copies that had *inverted* return values.

from unittest.mock import MagicMock, patch

import repo_utils
import parse_github_data


def _resp(status):
    r = MagicMock()
    r.status_code = status
    return r


def test_no_local_shadowing_of_repo_utils_helpers():
    # Regression: these must be the exact objects imported from repo_utils.
    assert parse_github_data.check_repo is repo_utils.check_repo
    assert parse_github_data.get_repo_name is repo_utils.get_repo_name


def test_check_repo_true_for_public_repo():
    with patch.object(repo_utils.requests, "head", return_value=_resp(200)):
        assert repo_utils.check_repo("https://github.com/owner/repo") is True


def test_check_repo_false_for_missing_repo():
    with patch.object(repo_utils.requests, "head", return_value=_resp(404)):
        assert repo_utils.check_repo("https://github.com/owner/missing") is False


def test_check_repo_false_for_non_url():
    assert repo_utils.check_repo("not-a-url") is False
    assert repo_utils.check_repo("") is False
    assert repo_utils.check_repo(None) is False


def test_check_repo_false_on_network_error():
    with patch.object(
        repo_utils.requests, "head",
        side_effect=repo_utils.requests.RequestException("boom"),
    ):
        assert repo_utils.check_repo("https://github.com/owner/repo") is False


def test_call_site_only_skips_bad_repos():
    # The call site is `if not check_repo(repo): continue`. With the correct
    # semantics, a healthy repo (True) is NOT skipped and a bad one (False) is.
    with patch.object(repo_utils.requests, "head", return_value=_resp(200)):
        assert not (not repo_utils.check_repo("https://github.com/o/r"))  # kept
    with patch.object(repo_utils.requests, "head", return_value=_resp(404)):
        assert (not repo_utils.check_repo("https://github.com/o/gone"))   # skipped
