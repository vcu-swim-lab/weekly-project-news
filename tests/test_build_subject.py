# Tests for fix #4 (and the empty-name robustness): build_subject is now a
# pure, deterministic function. It also documents that two subscribers to the
# same repo legitimately produce the SAME subject, which must no longer cause
# the second send to be skipped.

from datetime import datetime

import send_newsletter


def test_basic_subject():
    now = datetime(2026, 7, 12, 15, 30, 45)
    subject = send_newsletter.build_subject("https://github.com/ggml-org/llama.cpp", now)
    assert subject == (
        "Weekly GitHub Report for Llama.cpp: July 05, 2026 - July 12, 2026 (15:30:45)"
    )


def test_capitalizes_first_char_only():
    now = datetime(2026, 7, 12, 0, 0, 0)
    subject = send_newsletter.build_subject("https://github.com/owner/recorder", now)
    assert subject.startswith("Weekly GitHub Report for Recorder:")


def test_trailing_slash_does_not_crash():
    # Previously name[0].upper() raised IndexError when the repo name was empty.
    now = datetime(2026, 7, 12, 0, 0, 0)
    subject = send_newsletter.build_subject("https://github.com/owner/", now)
    assert "Weekly GitHub Report for" in subject


def test_empty_repo_does_not_crash():
    now = datetime(2026, 7, 12, 0, 0, 0)
    assert "Weekly GitHub Report for" in send_newsletter.build_subject("", now)
    assert "Weekly GitHub Report for" in send_newsletter.build_subject(None, now)


def test_same_repo_same_time_is_identical():
    # Regression for the removed subject-based dedup: identical subjects are
    # expected for multiple subscribers of one repo and are not an error.
    now = datetime(2026, 7, 12, 12, 0, 0)
    repo = "https://github.com/kubernetes/kubernetes"
    assert send_newsletter.build_subject(repo, now) == send_newsletter.build_subject(repo, now)
