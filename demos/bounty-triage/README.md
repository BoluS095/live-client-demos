# Bounty Triage — demo sample

A small, read-only Python CLI that screens a public GitHub issue before a developer invests time in a bounty. It flags closed issues, archived repositories, URLs that resolve to pull requests, stale activity, and open PRs that already cross-reference the issue.

This is an illustrative engineering sample, not client work. The included reports were generated from publicly visible GitHub records on 6 November 2026; no customer data is present.

## Run it

Requires Python 3.10+. No third-party packages are needed.

```bash
python3 bounty_triage.py https://github.com/OWNER/REPO/issues/123 --reward 42
```

Save the result as Markdown or JSON:

```bash
python3 bounty_triage.py https://github.com/OWNER/REPO/issues/123 \
  --reward 42 --markdown report.md --json report.json
```

A GitHub token is optional and can raise the public API rate limit. If provided through `GITHUB_TOKEN`, it is sent only to GitHub's API. The checker does not write to GitHub, claim rewards, send messages, create PRs, or initiate payments.

## Example results

- [rencfs](examples/rencfs.md): the bounty URL used `/issues/3`, but GitHub identifies it as an open PR; the timeline contains numerous competing PR references, so the checker says **SKIP**.
- [Cal.com](examples/calcom.md): the source issue is closed, so the checker says **SKIP**.
- [QTop](examples/qtop.md): the issue is open but already has an open cross-referenced PR, so the checker says **LOW PRIORITY** pending maintainer confirmation.

These examples are snapshots, not current guarantees. Always revisit the source issue and confirm reward availability and acceptance/payment terms directly before starting work.

## Checks and limitations

The tool checks the repository's archived flag, issue state and type, creation/update dates, labels, and public cross-referenced PRs from the issue timeline. The `--reward` value is reported as supplied; the tool does not independently verify escrow, the sponsor, eligibility, acceptance, or whether payment will be made. GitHub's public timeline may omit or truncate context, so manual review is still required.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
