from __future__ import annotations

import os
from pathlib import Path

import anthropic

from stackscan.models import ScanResult
from stackscan.scanners._util import parse_json_response
from stackscan.scanners.base import BaseScanner

_SYSTEM_PROMPT = """\
You are a Python application security scanner. Analyse the provided Python source files \
for security vulnerabilities and insecure coding patterns.

Return ONLY a JSON array of findings. No preamble, no explanation, no markdown code fences.
Each finding must be a JSON object with exactly these keys:
  "title"     - short one-line summary (string)
  "detail"    - explanation of the risk and the recommended fix (string)
  "severity"  - one of: critical, high, medium, low, info (string)
  "file_path" - relative path of the file where the issue was found (string or null)
  "line"      - approximate line number (integer or null)

Focus on: SQL injection, command injection, path traversal, insecure deserialization, \
hardcoded secrets or credentials, use of weak cryptography, improper input validation, \
SSRF, open redirects, insecure use of eval/exec, and missing authentication checks.

If no issues are found, return an empty JSON array: []"""

# Skip virtual environments and test fixtures
_SKIP_DIRS = {
    ".venv", "venv", "env", ".env", "site-packages",
    "__pycache__", ".git", "node_modules",
}

_MAX_FILES = 40  # cap to stay within token limits


class PythonScanner(BaseScanner):
    name = "python"
    category = "security"

    def collect(self, root_dir: str | Path) -> list[tuple[str, str]]:
        root = Path(root_dir)
        results: list[tuple[str, str]] = []

        for py_file in sorted(root.rglob("*.py")):
            # Skip excluded directories
            if any(part in _SKIP_DIRS for part in py_file.parts):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                results.append((str(py_file.relative_to(root)), content))
            except OSError:
                pass

            if len(results) >= _MAX_FILES:
                break

        return results

    def scan(self, root_dir: str | Path) -> list[ScanResult]:
        files = self.collect(root_dir)
        if not files:
            return []

        file_block = "\n\n".join(
            f"# File: {path}\n{content}" for path, content in files
        )

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": file_block}],
        )

        raw = message.content[0].text
        findings_data: list[dict] = parse_json_response(raw)

        return [
            ScanResult(
                scanner=self.name,
                category="security",
                severity=f["severity"],
                title=f["title"],
                detail=f["detail"],
                file_path=f.get("file_path"),
                line=f.get("line"),
            )
            for f in findings_data
        ]
