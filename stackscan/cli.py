#!/usr/bin/env python3
"""
stackscan CLI entry point.

Required environment variables:
  ANTHROPIC_API_KEY   – Anthropic API key (used by scanners)
  DASHBOARD_URL       – Base URL of the hosted dashboard
  DASHBOARD_TOKEN     – Bearer token for dashboard API auth

Optional environment variables:
  TARGET_DIR          – Directory to scan (default: current directory)
  GITHUB_REPOSITORY   – Set automatically by GitHub Actions (owner/repo)
  GITHUB_SHA          – Set automatically by GitHub Actions (commit SHA)
  GITHUB_OUTPUT       – Set automatically by GitHub Actions (output file path)
"""
from __future__ import annotations

import os
import sys

from stackscan.reporter import post_report
from stackscan.runner import run


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"[stackscan] ERROR: environment variable {name!r} is not set.", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    target_dir = os.environ.get("TARGET_DIR", ".")
    dashboard_url = _require_env("DASHBOARD_URL")
    dashboard_token = _require_env("DASHBOARD_TOKEN")

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    commit_sha = os.environ.get("GITHUB_SHA", "")

    print(f"[stackscan] target: {target_dir!r}", flush=True)
    print(f"[stackscan] repo:   {repo or '(not set)'}", flush=True)
    print(f"[stackscan] commit: {commit_sha or '(not set)'}", flush=True)

    report = run(target_dir, repo=repo, commit_sha=commit_sha)
    print(
        f"[stackscan] total findings: {len(report.findings)}",
        flush=True,
    )

    print("[stackscan] posting report to dashboard ...", flush=True)
    result = post_report(report, dashboard_url, dashboard_token)
    report_url: str = result.get("report_url", "")

    print(f"[stackscan] report URL: {report_url}", flush=True)

    # Export output for GitHub Actions
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as fh:
            fh.write(f"report_url={report_url}\n")
    else:
        print(f"report_url={report_url}")


if __name__ == "__main__":
    main()
