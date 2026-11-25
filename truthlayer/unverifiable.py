"""A6. Statements no specification can prove or disprove: HTTP headers and policies.
They are listed separately, with the booklet location, for a human to check."""
from __future__ import annotations
import re
from dataclasses import dataclass
from .docmap import Block, PROSE_KINDS

HEADER_WORD = re.compile(r"\bheaders?\b", re.I)
TOKEN = re.compile(r"`([A-Za-z][A-Za-z0-9-]*)`|\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b|\b([A-Z][A-Za-z]*(?:-[A-Za-z0-9]+)+)\b")
STOP_TOKENS = {"Bearer", "Authorization", "Content-Type", "Accept"}
POLICY = [
    (re.compile(r"(?i)\brate[- ]limit\w*|\b\d+\s+(?:requests?|calls?)\s+per\b"), "rate limit"),
    (re.compile(r"(?i)\b(?:access|refresh)?\s*tokens?\b[^.]{0,60}\b(?:expire|expires|expiry|valid for|lifetime)\b"), "token lifetime"),
    (re.compile(r"(?i)\b(?:four|4|\d+)\s+years?\s+of\b"), "data window"),
    (re.compile(r"(?i)\bterms of service\b|\bprivacy policy\b"), "policy document"),
    (re.compile(r"(?i)\bproduction access\b[^.]{0,80}\b(?:approval|review|requires?)\b"), "approval process"),
]


@dataclass
class Unverifiable:
    kind: str            # header | policy
    subject: str
    block_id: str
    file: str
    line: int
    section: str
    sentence: str


def find_unverifiable(blocks: list[Block]) -> list[Unverifiable]:
    out: list[Unverifiable] = []
    seen: set[tuple[str, str]] = set()
    for b in blocks:
        if b.kind not in PROSE_KINDS or b.file.endswith(".json"):
            continue
        for sent in re.split(r"(?<=[.!?])\s+", b.text):
            if HEADER_WORD.search(sent):
                for m in TOKEN.finditer(sent):
                    tok = next(g for g in m.groups() if g)
                    if tok in STOP_TOKENS or tok.lower() in ("header", "headers"):
                        continue
                    if (b.file, tok) not in seen:
                        seen.add((b.file, tok))
                        out.append(Unverifiable("header", tok, b.id, b.file, b.line, b.section, sent[:240]))
            for rx, label in POLICY:
                if rx.search(sent) and (b.file, sent[:60]) not in seen:
                    seen.add((b.file, sent[:60]))
                    out.append(Unverifiable("policy", label, b.id, b.file, b.line, b.section, sent[:240]))
    return out
