"""Small, checked edits for JSON sample passages.

The AI is asked for {old_text, new_text, reason} instead of a rewritten passage (a rewrite of a JSON sample is long,
runs into the output limit and gets cut off). The edit is applied in code and the result is checked to still be JSON.
"""
from __future__ import annotations

import json
import re
from typing import Any

EDIT_SYSTEM = ("You fix API documentation samples. You are given one JSON sample passage and the current v2 definition "
               "of the element it shows. Return the SMALLEST edit that makes the sample match v2. Reply with JSON only: "
               '{"old_text": "<exact text from the passage, appearing exactly once>", "new_text": "<replacement>", '
               '"reason": "<at most 20 words>"}. If nothing in the sample is wrong, return empty old_text and new_text. '
               "Never repeat the whole passage.")


def parse_edit_reply(text: str) -> tuple[str, str, str, str]:
    """(old_text, new_text, reason, error). error is '' when the reply was readable."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return "", "", "", "unparseable reply"
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return "", "", "", "unparseable reply"
    if not isinstance(d, dict) or not all(isinstance(d.get(k, ""), str) for k in ("old_text", "new_text")):
        return "", "", "", "unparseable reply"
    reason = " ".join(str(d.get("reason", "")).split()[:30])
    return d.get("old_text", ""), d.get("new_text", ""), reason, ""


def apply_edit(passage: str, old: str, new: str) -> tuple[str, str]:
    """(new_passage, error). The old text must be found exactly once."""
    if not old:
        return passage, ""
    n = passage.count(old)
    if n == 0:
        return passage, "old_text not found in the passage"
    if n > 1:
        return passage, f"old_text appears {n} times; it must be unique"
    return passage.replace(old, new, 1), ""


def loose_json_ok(text: str) -> bool:
    """A passage may be a fragment of a JSON document: accept it if it is JSON on its own, or inside {} or []."""
    t = text.strip().rstrip(",")
    for wrap in ("{}", "[]"):
        for candidate in (t, wrap[0] + t + wrap[1]):
            try:
                json.loads(candidate)
                return True
            except json.JSONDecodeError:
                pass
    return False


def _shape(text: str) -> tuple[int, int, int]:
    return text.count("{") - text.count("}"), text.count("[") - text.count("]"), text.count('"') % 2


def validate_fragment_edit(before: str, after: str) -> str:
    """'' if the edit keeps a fragment as valid as it was. Strict when the fragment is JSON; otherwise the
    bracket and quote balance must not change."""
    if loose_json_ok(before):
        return "" if loose_json_ok(after) else "the edit would make the sample invalid JSON"
    return "" if _shape(before) == _shape(after) else "the edit changes the bracket or quote balance of the sample"


def validate_file_edit(full_text: str, lo: int, hi: int, new_passage: str) -> str:
    """'' if replacing lines lo..hi of a whole JSON file with new_passage keeps it valid JSON."""
    lines = full_text.split("\n")
    new_text = "\n".join(lines[:lo - 1] + new_passage.split("\n") + lines[hi:])
    try:
        json.loads(new_text)
    except json.JSONDecodeError as exc:
        return f"the edit would make the file invalid JSON ({exc.msg})"
    return ""


def edit_from_rewrite(original: str, proposed: str) -> dict[str, str] | None:
    """Turn a whole-passage rewrite into the smallest old/new edit (None if nothing changed)."""
    if original == proposed:
        return None
    p = 0
    while p < min(len(original), len(proposed)) and original[p] == proposed[p]:
        p += 1
    s = 0
    while s < min(len(original), len(proposed)) - p and original[-1 - s] == proposed[-1 - s]:
        s += 1
    lo, hi_o, hi_n = p, len(original) - s, len(proposed) - s
    ctx = 12
    while True:
        a, b = max(0, lo - ctx), min(len(original), hi_o + ctx)
        old = original[a:b]
        new = proposed[a:hi_n + (b - hi_o)]       # the text before position p is identical in both strings
        if old and original.count(old) == 1:
            return {"old_text": old, "new_text": new}
        if ctx > len(original):
            return {"old_text": original, "new_text": proposed}
        ctx *= 2


def mock_sample_edit(token: str, new_name: str, passage: str) -> dict[str, Any]:
    """MOCK stand-in: rename a JSON key when there is exactly one occurrence of it."""
    old = f'"{token}"'
    if new_name and passage.count(old) == 1:
        return {"old_text": old, "new_text": f'"{new_name}"'}
    return {"old_text": "", "new_text": ""}
