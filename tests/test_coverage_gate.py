# Tests for the coverage gate that makes parse_github_data fail loudly (non-zero
# exit) when it populates far fewer repositories than attempted, instead of
# silently letting the pipeline send empty newsletters.

import parse_github_data


def test_all_succeeded_passes():
    assert parse_github_data.coverage_check_failed(22, 0) is False


def test_small_minority_failures_pass():
    # A few flaky repos should NOT abort the whole pipeline.
    assert parse_github_data.coverage_check_failed(19, 3) is False


def test_exactly_half_failed_passes():
    # Half failing is tolerated; only a strict majority trips the gate.
    assert parse_github_data.coverage_check_failed(11, 11) is False


def test_majority_failed_fails():
    assert parse_github_data.coverage_check_failed(10, 12) is True


def test_last_nights_scenario_fails():
    # ~2 populated of 22 attempted -> must fail.
    assert parse_github_data.coverage_check_failed(2, 20) is True


def test_nothing_succeeded_fails():
    assert parse_github_data.coverage_check_failed(0, 5) is True


def test_nothing_attempted_does_not_fail():
    # No public repos to process is not a parse failure (avoids a crash/abort
    # when the subscriber list is empty).
    assert parse_github_data.coverage_check_failed(0, 0) is False
