from __future__ import annotations

import os
from pathlib import Path

import anthropic

from stackscan.models import ScanResult
from stackscan.scanners._util import parse_json_response
from stackscan.scanners.base import BaseScanner

_SYSTEM_PROMPT = """\
You are a Terraform security scanner. Analyse the provided Terraform source files \
for security vulnerabilities, misconfigurations, and compliance issues.

Return ONLY a JSON array of findings. No preamble, no explanation, no markdown code fences.
Each finding must be a JSON object with exactly these keys:
  "title"     - short one-line summary (string)
  "detail"    - explanation of the risk and the recommended fix (string)
  "severity"  - one of: critical, high, medium, low, info (string)
  "file_path" - relative path of the file where the issue was found (string or null)
  "line"      - approximate line number (integer or null)

Focus on: open security groups, public S3 buckets, missing encryption, \
overly-permissive IAM, unversioned state buckets, missing audit logging, \
hardcoded secrets, and insecure defaults.

If no issues are found, return an empty JSON array: []"""


class TerraformScanner(BaseScanner):
    name = "terraform"
    category = "security"

    def collect(self, root_dir: str | Path) -> list[tuple[str, str]]:
        root = Path(root_dir)
        results: list[tuple[str, str]] = []
        for tf_file in sorted(root.rglob("*.tf")):
            try:
                content = tf_file.read_text(encoding="utf-8", errors="replace")
                results.append((str(tf_file.relative_to(root)), content))
            except OSError:
                pass
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
