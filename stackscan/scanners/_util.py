from __future__ import annotations

import json
import re


def parse_json_response(text: str) -> list[dict]:
    """
    Parse a JSON array from a Claude response, tolerating markdown code fences.

    Claude occasionally wraps output in ```json ... ``` blocks despite being
    instructed not to.  This strips any such fencing before parsing.
    """
    text = text.strip()

    # Strip ```json ... ``` or ``` ... ``` fences
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()

    if not text:
        return []

    return json.loads(text)
