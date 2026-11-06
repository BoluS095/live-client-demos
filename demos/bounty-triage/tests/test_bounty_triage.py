import datetime as dt
import unittest

from bounty_triage import inspect_bounty, parse_issue_url


class BountyTriageTests(unittest.TestCase):
    def test_parse_canonical_issue_url(self):
        ref = parse_issue_url("https://github.com/example/project/issues/123")
        self.assertEqual((ref.owner, ref.repo, ref.number, ref.kind), ("example", "project", 123, "issues"))

    def test_parse_pull_request_url(self):
        ref = parse_issue_url("https://github.com/example/project/pull/9/")
        self.assertEqual(ref.kind, "pull")
        self.assertEqual(ref.number, 9)

    def test_rejects_noncanonical_or_non_github_url(self):
        for url in (
            "https://github.com/example/project/issues/1?tab=comments",
            "https://github.com.evil.test/example/project/issues/1",
            "http://github.com/example/project/issues/1",
            "https://github.com/example/project",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_issue_url(url)

    def test_closed_archived_and_pull_request_are_hard_stops(self):
        payloads = {
            "/repos/example/project": {"archived": True},
            "/repos/example/project/issues/4": {
                "number": 4,
                "title": "Already done",
                "state": "closed",
                "pull_request": {"url": "https://api.github.com/repos/example/project/pulls/4"},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
                "labels": [],
            },
            "/repos/example/project/issues/4/timeline?per_page=100": [],
        }

        def fake_get(path, token=None):
            return payloads[path]

        result = inspect_bounty(
            "https://github.com/example/project/issues/4",
            reward_usd=42,
            now=dt.datetime(2026, 11, 6, tzinfo=dt.timezone.utc),
            api_get=fake_get,
        )
        self.assertEqual(result["recommendation"], "SKIP")
        self.assertTrue(result["repository_archived"])
        self.assertTrue(result["is_pull_request"])
        self.assertEqual(len(result["hard_stops"]), 3)

    def test_open_cross_referenced_pr_lowers_priority(self):
        payloads = {
            "/repos/example/project": {"archived": False},
            "/repos/example/project/issues/7": {
                "number": 7,
                "title": "Implement feature",
                "state": "open",
                "created_at": "2026-10-20T00:00:00Z",
                "updated_at": "2026-11-01T00:00:00Z",
                "labels": [{"name": "$100"}],
            },
            "/repos/example/project/issues/7/timeline?per_page=100": [
                {
                    "event": "cross-referenced",
                    "source": {
                        "issue": {
                            "number": 19,
                            "title": "First attempt",
                            "state": "open",
                            "html_url": "https://github.com/example/project/pull/19",
                            "pull_request": {},
                        }
                    },
                }
            ],
        }

        def fake_get(path, token=None):
            return payloads[path]

        result = inspect_bounty(
            "https://github.com/example/project/issues/7",
            reward_usd=100,
            now=dt.datetime(2026, 11, 6, tzinfo=dt.timezone.utc),
            api_get=fake_get,
        )
        self.assertIn("LOW PRIORITY", result["recommendation"])
        self.assertEqual(result["open_cross_referenced_prs"][0]["number"], 19)
        self.assertTrue(result["read_only"])

    def test_timeline_failure_is_reported_as_warning_not_a_false_clean_bill(self):
        def fake_get(path, token=None):
            if path.endswith("/timeline?per_page=100"):
                raise RuntimeError("timeline unavailable")
            if path == "/repos/example/project":
                return {"archived": False}
            return {
                "number": 3,
                "title": "Test issue",
                "state": "open",
                "created_at": "2026-11-01T00:00:00Z",
                "updated_at": "2026-11-05T00:00:00Z",
                "labels": [],
            }

        # The production client raises GitHubError; this makes the test independent of HTTP.
        from bounty_triage import GitHubError

        def wrapped_get(path, token=None):
            try:
                return fake_get(path, token)
            except RuntimeError as exc:
                raise GitHubError(str(exc)) from exc

        result = inspect_bounty(
            "https://github.com/example/project/issues/3",
            now=dt.datetime(2026, 11, 6, tzinfo=dt.timezone.utc),
            api_get=wrapped_get,
        )
        self.assertTrue(any("Could not check issue cross-references" in w for w in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
