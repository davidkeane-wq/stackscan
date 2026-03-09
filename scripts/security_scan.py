import os
import sys
import json
import anthropic
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
SKIP_DIRS = {"venv", ".terraform", "__pycache__", ".git", "node_modules", ".pytest_cache"}
SCAN_EXTENSIONS = {".py", ".tf"}


def collect_files(root: Path) -> dict[str, str]:
    """Walk the repo and return {relative_path: file_contents}"""
    files = {}
    for path in root.rglob("*"):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.suffix not in SCAN_EXTENSIONS:
            continue
        if not path.is_file():
            continue
        try:
            files[str(path.relative_to(root))] = path.read_text()
        except Exception:
            pass
    return files


def build_prompt(files: dict[str, str]) -> str:
    file_contents = ""
    for filename, contents in files.items():
        file_contents += f"\n\n### FILE: {filename}\n```\n{contents}\n```"

    return f"""You are a security auditor reviewing code and infrastructure for vulnerabilities.

Analyse the following files for security issues. Look for:

PYTHON CODE:
- Hardcoded secrets, tokens, or passwords
- Overly permissive CORS configuration
- Missing authentication or authorisation on endpoints
- Insecure dependencies or imports
- Injection vulnerabilities
- Sensitive data exposure

TERRAFORM / INFRASTRUCTURE:
- Overly permissive IAM roles
- Publicly accessible resources that shouldn't be
- Missing resource limits (could cause unexpected costs)
- Unencrypted storage or data in transit
- Missing logging or monitoring
- Open ingress/egress rules

For each finding return a severity of either: critical, warning, or info.

You MUST respond with ONLY a valid JSON object — no preamble, no explanation, no markdown.
The JSON must match this exact structure:
{{
  "findings": [
    {{
      "severity": "critical|warning|info",
      "category": "string (e.g. secrets, iam, cors, auth)",
      "file": "relative path to file",
      "issue": "clear description of the problem",
      "recommendation": "specific actionable fix"
    }}
  ],
  "summary": "X critical, X warning, X info"
}}

If no issues are found return an empty findings array.

FILES TO ANALYSE:
{file_contents}"""


def run_scan(prompt: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw = message.content[0].text

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())


def write_report(results: dict, commit_sha: str) -> str:
    report = {
        "commit_sha": commit_sha,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        **results
    }

    output_path = Path("/tmp/scan_report.json")
    output_path.write_text(json.dumps(report, indent=2))
    print(f"Report written to {output_path}")
    print(f"Summary: {results.get('summary', 'no summary')}")

    # Print findings to pipeline logs too
    for finding in results.get("findings", []):
        icon = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(finding["severity"], "⚪")
        print(f"{icon} {finding['severity'].upper()} — {finding['file']}: {finding['issue']}")

    return str(output_path)

if __name__ == "__main__":
    commit_sha = os.environ.get("GITHUB_SHA", "local")

    print("Collecting files...")
    files = collect_files(REPO_ROOT)
    print(f"Found {len(files)} files to scan: {list(files.keys())}")

    print("Building prompt and calling Claude...")
    prompt = build_prompt(files)
    results = run_scan(prompt)

    write_report(results, commit_sha)
    print("Scan complete.")