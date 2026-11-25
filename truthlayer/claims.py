"""Does a booklet passage STATE something about the rule that changed?

WRONG needs the text to say something that is now false. A passage that only names a field
(a list item, a table cell, a heading) makes no claim, so it only NEEDS_NOTE: a writer should add the new rule.
This is a plain word check on the changed kinds (cardinality, value set, type, ...), not AI.
"""
from __future__ import annotations

import re

CLAIM_WORDS: dict[str, re.Pattern[str]] = {
    "cardinality": re.compile(r"(?i)\b(optional|required|mandatory|must|always|never|may be (?:omitted|absent|empty)|one or more|zero or"
                              r"|at least|at most|exactly|only one|multiple|repeat\w*|can be omitted|not required)\b|\b[01]\.\.[1*]\b"),
    "value_set": re.compile(r"(?i)\b(value ?sets?|code ?systems?|codes?|allowed values?|one of|enumerat\w*|possible values?)\b"),
    "type": re.compile(r"(?i)\b(data ?type|type of|string|boolean|integer|date ?time|date|code ?able ?concept|coding|quantity|period)\b"),
    "target_type": re.compile(r"(?i)\b(references?|refers? to|points? to|links? to)\b"),
    "fixed_default": re.compile(r"(?i)\b(default\w*|fixed|always set to)\b"),
    "profile": re.compile(r"(?i)\b(must[- ]support\w*|slic\w+|discriminator|profile)\b"),
}

KIND_TO_CLAIM = {
    "cardinality": "cardinality", "now_required": "cardinality", "profile_cardinality": "cardinality",
    "profile_now_required": "cardinality",
    "value_set": "value_set", "value_set_version": "value_set", "binding_strength": "value_set",
    "profile_value_set": "value_set", "profile_binding_strength": "value_set",
    "type": "type", "profile_type": "type",
    "target_type": "target_type", "profile_target_type": "target_type",
    "fixed_default": "fixed_default", "profile_fixed_default": "fixed_default",
    "must_support": "profile", "slicing": "profile",
}


def makes_claim(sub_kinds: list[str], passage: str) -> bool:
    """True if the passage says something about ANY of the rules that changed."""
    needed = {KIND_TO_CLAIM[k] for k in sub_kinds if k in KIND_TO_CLAIM}
    if not needed:
        return True          # unknown kind of change: stay cautious and keep it as WRONG
    return any(CLAIM_WORDS[c].search(passage) for c in needed)
