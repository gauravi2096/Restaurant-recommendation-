"""
Response parser: extract clean summary text from LLM output.
"""

from __future__ import annotations

import re


def parse_summary(raw_content: str | None) -> str:
    """
    Parse the raw LLM response into a single summary string.

    - Strips leading/trailing whitespace.
    - If the model wrapped in markdown (e.g. ``` ... ```), unwraps.
    - Returns empty string if input is None or empty after strip.
    """
    if not raw_content:
        return ""
    text = raw_content.strip()
    if not text:
        return ""

    # Remove optional markdown code fence wrapper
    fence = re.match(r"^```(?:\w*)\s*\n?(.*?)\n?```\s*$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    return text
