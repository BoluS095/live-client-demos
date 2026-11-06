#!/usr/bin/env python3
"""Read-only GitHub bounty due diligence.

Checks a public GitHub issue and repository before anyone spends time on a bounty.
No comments, claims, PRs, account changes, or payments are made.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any

GITHUB_API = "https://api.github.com"
ISSUE_URL_RE = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/(issues|pull)/(\d+)/?$",
    re.IGNORECASE,
)


class GitHubError(RuntimeError):
    """A public GitHub API request failed."""


@dataclass(frozen=True)
class IssueRef:
    owner: str
    repo: str
    number: int
    kind: str

    @property
    def repository(self) -> str:
        return f"{self.owner}/{self.repo}"


def parse_issue_url(url: str) -> IssueRef:
    """Accept only a canonical GitHub issue or pull-request URL."""
    match = ISSUE_URL_RE.fullmatch(url.strip())
    if not match:
        raise ValueError(
            "Expected https://github.com/OWNER/REPO/issues/NUMBER "
            "or https://github.com/OWNER/REPO/pull/NUMBER"
        )
    owner, repo, kind, number = match.groups()
    return IssueRef(owner, repo, int(number), kind.lower())


def _iso_to_dt(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _api_get(path: str, token: str | None = None, timeout: float = 20) -> Any:
    url = f"{GITHUB_API}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "bounty-triage-readonly/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise GitHubError(f"GitHub API returned HTTP {exc.code} for {path}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GitHubError(f"Could not reach GitHub API for {path}: {exc}") from exc


def inspect_bounty(
    issue_url: str,
    reward_usd: float | None = None,
    *,
    now: dt.datetime | None = None,
    api_get=_api_get,
    token: str | None = None,
) -> dict[str, Any]:
    """Fetch public issue/repo/timeline data and return a conservative triage."""
    ref = parse_issue_url(issue_url)
    now = now or dt.datetime.now(dt.timezone.utc)
    prefix = f"/repos/{ref.owner}/{ref.repo}"

    repo_data = api_get(prefix, token)
    issue_data = api_get(f"{prefix}/issues/{ref.number}", token)
    timeline: list[dict[str, Any]] = []
    timeline_error: str | None = None
    try:
        timeline = api_get(f"{prefix}/issues/{ref.number}/timeline?per_page=100", token)
        if not isinstance(timeline, list):
            timeline = []
    except GitHubError as exc:
        timeline_error = str(exc)

    created = _iso_to_dt(issue_data.get("created_at"))
    updated = _iso_to_dt(issue_data.get("updated_at"))
    age_days = max(0, (now - created).days) if created else None
    days_since_update = max(0, (now - updated).days) if updated else None
    is_pull_request = "pull_request" in issue_data
    state = issue_data.get("state", "unknown")
    repo_archived = bool(repo_data.get("archived", False))

    open_prs: dict[int, dict[str, str]] = {}
    closed_prs: dict[int, dict[str, str]] = {}
    for event in timeline:
        if event.get("event") != "cross-referenced":
            continue
        source = (event.get("source") or {}).get("issue") or {}
        if "pull_request" not in source:
            continue
        try:
            number = int(source.get("number"))
        except (TypeError, ValueError):
            continue
        record = {
            "number": number,
            "title": str(source.get("title", "")),
            "url": str(source.get("html_url", "")),
            "state": str(source.get("state", "unknown")),
        }
        if record["state"] == "open":
            open_prs[number] = record
        else:
            closed_prs[number] = record

    labels = [str(label.get("name", "")) for label in issue_data.get("labels", [])]
    hard_stops: list[str] = []
    warnings: list[str] = []
    if state != "open":
        hard_stops.append(f"Source item is {state}, not open.")
    if repo_archived:
        hard_stops.append("Repository is archived/read-only.")
    if is_pull_request:
        hard_stops.append("The supplied /issues/ URL is actually a pull request, not an issue.")
    if open_prs:
        warnings.append(f"{len(open_prs)} open pull request(s) already cross-reference this issue.")
    if days_since_update is not None and days_since_update > 90:
        warnings.append(f"Issue has not been updated for {days_since_update} days.")
    if age_days is not None and age_days > 365:
        warnings.append(f"Issue is {age_days} days old; confirm the reward is still funded.")
    if reward_usd is None:
        warnings.append("Reward amount was not independently supplied to this checker.")
    if timeline_error:
        warnings.append("Could not check issue cross-references; manually inspect linked PRs.")

    if hard_stops:
        recommendation = "SKIP"
    elif open_prs or (days_since_update is not None and days_since_update > 90):
        recommendation = "LOW PRIORITY — verify with the maintainer before building"
    else:
        recommendation = "POTENTIALLY ACTIONABLE — review acceptance criteria and payment terms"

    return {
        "source_url": issue_url,
        "repository": ref.repository,
        "issue_number": ref.number,
        "title": issue_data.get("title", ""),
        "state": state,
        "is_pull_request": is_pull_request,
        "repository_archived": repo_archived,
        "reward_usd": reward_usd,
        "created_at": issue_data.get("created_at"),
        "updated_at": issue_data.get("updated_at"),
        "age_days": age_days,
        "days_since_update": days_since_update,
        "labels": labels,
        "open_cross_referenced_prs": sorted(open_prs.values(), key=lambda row: row["number"]),
        "closed_cross_referenced_prs": sorted(closed_prs.values(), key=lambda row: row["number"]),
        "timeline_check_error": timeline_error,
        "hard_stops": hard_stops,
        "warnings": warnings,
        "recommendation": recommendation,
        "checked_at": now.isoformat(),
        "read_only": True,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"## {result['recommendation']}: {result['title']}",
        "",
        f"- Source: {result['source_url']}",
        f"- Repository: `{result['repository']}` (archived: {result['repository_archived']})",
        f"- GitHub state: **{result['state']}**; pull request URL: {result['is_pull_request']}",
        f"- Reward provided: {('$' + format(result['reward_usd'], '.2f')) if result['reward_usd'] is not None else 'not provided'}",
        f"- Created: {result['created_at']}; last updated: {result['updated_at']}",
    ]
    if result["hard_stops"]:
        lines += ["", "**Stop conditions**"]
        lines += [f"- {item}" for item in result["hard_stops"]]
    if result["warnings"]:
        lines += ["", "**Warnings**"]
        lines += [f"- {item}" for item in result["warnings"]]
    if result["open_cross_referenced_prs"]:
        lines += ["", "**Already open PRs referencing this issue**"]
        for pr in result["open_cross_referenced_prs"]:
            lines.append(f"- [#{pr['number']} {pr['title']}]({pr['url']})")
    lines += ["", "This check only reads public GitHub data; it does not claim, comment, submit work, or guarantee payment."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue_url", help="Canonical public GitHub issue or PR URL")
    parser.add_argument("--reward", type=float, help="Advertised reward in USD; reported as provided, not verified")
    parser.add_argument("--json", dest="json_path", help="Write structured output to this file")
    parser.add_argument("--markdown", dest="markdown_path", help="Write a Markdown summary to this file")
    args = parser.parse_args(argv)
    try:
        result = inspect_bounty(args.issue_url, args.reward, token=os.getenv("GITHUB_TOKEN"))
    except (ValueError, GitHubError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(render_markdown(result))
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    if args.markdown_path:
        with open(args.markdown_path, "w", encoding="utf-8") as handle:
            handle.write(render_markdown(result) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
