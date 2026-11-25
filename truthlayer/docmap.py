"""1C. Turn the old booklet (Markdown with HTML blocks) into located pieces and find element mentions."""
from __future__ import annotations
import json, re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from .fhir_adapter import Element

PROSE_KINDS = ("prose", "list_item", "table")
SAMPLE_KINDS = ("sample", "code")
RESOURCES = ("Patient", "Coverage", "ExplanationOfBenefit")
RES_ALIASES = {"eob": "ExplanationOfBenefit", "explanationofbenefit": "ExplanationOfBenefit",
               "explanation of benefit": "ExplanationOfBenefit", "explanation of benefits": "ExplanationOfBenefit",
               "patient": "Patient", "coverage": "Coverage"}


@dataclass
class Block:
    id: str
    file: str
    line: int          # first line (1-based)
    end_line: int
    section: str       # heading chain, e.g. "Core Resources > Item"
    kind: str          # prose | list_item | table | code | sample
    text: str
    resource_hint: str = ""   # resource named in a sample, if any

    def to_dict(self):
        return asdict(self)


@dataclass
class Mention:
    block_id: str
    file: str
    line: int
    section: str
    kind: str
    token: str
    candidates: list[str]      # v1 element paths, search params or resource types
    category: str = "element"  # element | search_param | resource
    ambiguous: bool = False
    text: str = ""
    evidence: str = ""         # path | json_path | field_list | field_table | named_in_context | search_param | resource

    def to_dict(self):
        return asdict(self)


def _heading_level(line: str):
    m = re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
    if m:
        return len(m.group(1)), m.group(2)
    m = re.match(r"^\s*<h([1-6])[^>]*>(.*?)</h\1>\s*$", line, re.I)
    if m:
        return int(m.group(1)), re.sub(r"<[^>]+>", "", m.group(2)).strip()
    return None


def _strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def parse_markdown(path: Path, display: str | None = None) -> list[Block]:
    name = display or str(path)
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    blocks: list[Block] = []
    chain: list[tuple[int, str]] = []
    i, n = 0, len(lines)
    para: list[tuple[int, str]] = []

    def section():
        return " > ".join(t for _, t in chain)

    def add(kind, start, end, text, hint=""):
        blocks.append(Block(f"{Path(name).stem}:{len(blocks)+1}", name, start, end, section(), kind, text, hint))

    def flush():
        nonlocal para
        if para:
            text = " ".join(t.strip() for _, t in para)
            if _strip_tags(text):
                add("prose", para[0][0], para[-1][0], _strip_tags(text) if text.lstrip().startswith("<") else text)
            para = []

    in_pre = False
    pre_start = 0
    pre_buf: list[str] = []
    while i < n:
        raw = lines[i]
        ln = i + 1
        s = raw.strip()
        # fenced code
        if s.startswith("```"):
            flush()
            j = i + 1
            body = []
            while j < n and not lines[j].strip().startswith("```"):
                body.append(lines[j]); j += 1
            add("sample" if re.search(r'"\w+"\s*:', "\n".join(body)) or "{" in "\n".join(body) else "code",
                ln, j + 1, "\n".join(body), _resource_hint("\n".join(body)))
            i = j + 1
            continue
        # <pre> block (possibly multi-line)
        if re.match(r"<pre\b", s, re.I):
            flush()
            j = i
            body = []
            while j < n:
                body.append(lines[j])
                if re.search(r"</pre>", lines[j], re.I):
                    break
                j += 1
            txt = re.sub(r"</?pre[^>]*>", "", "\n".join(body), flags=re.I)
            txt = txt.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
            add("sample" if re.search(r'"\w+"\s*:', txt) else "code", ln, j + 1, txt.strip("\n"), _resource_hint(txt))
            i = j + 1
            continue
        h = _heading_level(raw)
        if h:
            flush()
            lvl, title = h
            while chain and chain[-1][0] >= lvl:
                chain.pop()
            chain.append((lvl, title))
            i += 1
            continue
        if not s:
            flush(); i += 1; continue
        if s.startswith("|") and s.endswith("|"):
            flush()
            if not re.match(r"^\|[\s:\-|]+\|$", s):
                add("table", ln, ln, s)
            i += 1
            continue
        if re.match(r"^(</?(table|thead|tbody|tr|td|th)\b)", s, re.I) or re.match(r"^<t[dh]\b", s, re.I):
            flush()
            t = _strip_tags(s)
            if t:
                add("table", ln, ln, t)
            i += 1
            continue
        if re.match(r"^([-*+]|\d+[.)])\s+", s):
            flush()
            add("list_item", ln, ln, re.sub(r"^([-*+]|\d+[.)])\s+", "", s))
            i += 1
            continue
        if re.match(r"^</?(div|p|span|img|ul|ol|br|hr)\b", s, re.I) and not _strip_tags(s):
            flush(); i += 1; continue
        para.append((ln, raw))
        i += 1
    flush()
    return blocks


def _resource_hint(text: str) -> str:
    m = re.search(r'"resourceType"\s*:\s*"(\w+)"', text)
    return m.group(1) if m else ""


def json_keys(text: str, root_hint: str = "") -> list[tuple[int, str, list[str], str]]:
    """Walk pretty-printed JSON (or a fragment of it) line by line.
    Returns (line_offset, key, path_parts_below_resource, resource_root_or_empty)."""
    out = []
    stack: list[str] = []                 # keys of open containers ("" for anonymous objects)
    roots: list[tuple[int, str]] = []     # (stack depth where the resource starts, resource name)
    for off, raw in enumerate(text.split("\n")):
        s = raw.strip()
        m = re.match(r'^"([^"]+)"\s*:\s*(.*)$', s)
        if m:
            k, rest = m.group(1), m.group(2)
            if k == "resourceType":
                v = re.match(r'"(\w+)"', rest)
                if v:
                    roots.append((len(stack), v.group(1)))
                continue
            base, root = (roots[-1] if roots else (0, root_hint))
            parts = [p for p in stack[base:] if p] + [k]
            out.append((off, k, parts, root))
            r = rest.rstrip(",")
            if (r.startswith("{") and not r.endswith("}")) or (r.startswith("[") and not r.endswith("]")):
                stack.append(k)
            continue
        r = s.rstrip(",")
        if r.startswith("{") and not r.endswith("}"):
            stack.append("")
        elif s.startswith("}") or s.startswith("]"):
            if stack:
                stack.pop()
            while roots and roots[-1][0] > len(stack):
                roots.pop()
    return out


def parse_json_sample(path: Path, display: str | None = None) -> Block:
    name = display or str(path)
    text = Path(path).read_text(encoding="utf-8")
    return Block(f"{Path(name).stem}:1", name, 1, len(text.split("\n")), "sample file", "sample", text, "")


# ---------------------------------------------------------------- mentions
def _words(s: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[A-Za-z]+", s)}


class Index:
    """Lookup of v1 elements / search params / resource types for resolving names."""

    def __init__(self, v1: dict[str, Element], search_params: dict[str, set[str]],
                 gone_types: set[str]):
        self.v1 = v1
        self.by_name: dict[str, list[str]] = {}
        for p, e in v1.items():
            self.by_name.setdefault(e.name.replace("[x]", "").lower(), []).append(p)
        self.choice = [(p, e.name.replace("[x]", "")) for p, e in v1.items() if e.name.endswith("[x]")]
        self.search_params = search_params          # resource -> names (v1)
        self.all_search = {s for v in search_params.values() for s in v}
        self.gone_types = gone_types

    def resolve_name(self, name: str, ctx_resources: list[str], heading_words: set[str], choice: bool = True):
        key = name.lower()
        cands = list(self.by_name.get(key, []))
        for p, base in (self.choice if choice else []):      # servicedPeriod -> serviced[x]
            if name.startswith(base) and len(name) > len(base) and name[len(base)].isupper():
                cands.append(p)
        if not cands:
            return [], False
        if ctx_resources:
            inctx = [c for c in cands if c.split(".")[0] in ctx_resources]
            cands = inctx or cands
        if len(cands) > 1:
            by_parent = [c for c in cands if c.split(".")[-2].lower() in heading_words] if all("." in c for c in cands) else []
            if by_parent:
                cands = by_parent
        if len(cands) > 1:
            shallow = min(c.count(".") for c in cands)
            cands = [c for c in cands if c.count(".") == shallow]
        return cands, len(cands) > 1

    @staticmethod
    def _seg_eq(v1seg: str, part: str) -> bool:
        if v1seg == part:
            return True
        if v1seg.endswith("[x]"):
            base = v1seg[:-3]
            return part.startswith(base) and len(part) > len(base) and part[len(base)].isupper()
        return False

    def match_parts(self, parts: list[str], root: str = "") -> list[str]:
        """Exact (resource-rooted) or suffix match of a JSON key path against v1 element paths."""
        out = []
        for p in self.v1:
            segs = p.split(".")
            if root:
                if segs[0] != root or len(segs) - 1 != len(parts):
                    continue
                tail = segs[1:]
            else:
                if len(parts) < 2 or len(segs) - 1 < len(parts):
                    continue
                tail = segs[-len(parts):]
            if all(self._seg_eq(a, b) for a, b in zip(tail, parts)):
                out.append(p)
        return out

    def resolve_path(self, tok: str):
        t = tok.strip("`. ")
        parts = t.split(".")
        if len(parts) < 2:
            return []
        parts[0] = {"eob": "ExplanationOfBenefit"}.get(parts[0].lower(), parts[0])
        tail = ".".join(parts).lower()
        return [p for p in self.v1 if p.lower() == tail or p.lower().endswith("." + tail)]


IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_\-]*(?:\.[A-Za-z_][A-Za-z0-9_\[\]\-]*)*")
COMMON_WORDS = {"patient", "status", "type", "code", "use", "name", "value", "system", "text", "id",
                "identifier", "resource", "reference", "display", "period", "date", "subject", "category"}
GENERIC_WORDS = {"resourceType", "fullUrl", "lastUpdated"}   # JSON plumbing words, not element names
CAMEL = re.compile(r"^[a-z]+(?:[A-Z][a-z0-9]*)+$")


def block_context(block: Block, title: str) -> tuple[list[str], set[str]]:
    ctx: list[str] = []
    text = " ".join([title, block.section]).lower()
    for alias, res in RES_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", text) and res not in ctx:
            ctx.append(res)
    if block.resource_hint in RESOURCES:
        ctx = [block.resource_hint]
    return ctx, _words(block.section)


def resources_in(text: str) -> list[str]:
    """Resources named in a piece of text (Patient, Coverage, ExplanationOfBenefit / "Explanation of Benefit" / EOB)."""
    low = text.lower()
    out: list[str] = []
    for alias, res in RES_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"s?\b", low) and res not in out:
            out.append(res)
    return out


def find_mentions(blocks: list[Block], idx: Index, titles: dict[str, str]) -> list[Mention]:
    """Link booklet passages to elements, but only when the passage context fits:
    a full dotted path, a JSON path, a field list/table under the right resource or parent element,
    or a lowerCamel name with its resource named in the same passage / heading / the two blocks before."""
    out: list[Mention] = []
    seen: set[tuple] = set()

    def emit(b, line, token, cands, cat="element", amb=False, kind=None, evidence=""):
        k = (b.id, line, token, tuple(cands))
        if k in seen or not cands:
            return
        seen.add(k)
        out.append(Mention(b.id, b.file, line, b.section, kind or b.kind, token, cands, cat, amb,
                           b.text.split("\n")[max(0, line - b.line)][:200] if b.kind in SAMPLE_KINDS else b.text[:200],
                           evidence))

    by_file: dict[str, list[Block]] = {}
    for blk in blocks:
        by_file.setdefault(blk.file, []).append(blk)
    pos = {blk.id: (blk.file, i) for f, bl in by_file.items() for i, blk in enumerate(bl)}

    for b in blocks:
        ctx, hw = block_context(b, titles.get(b.file, ""))
        f, i = pos[b.id]
        near = set(resources_in(b.text + " " + b.section))
        for prev in by_file[f][max(0, i - 2):i]:
            if prev.kind in PROSE_KINDS:
                near |= set(resources_in(prev.text))
        # whole-resource-name mentions (e.g. a resource that no longer exists)
        for g in idx.gone_types:
            for m in re.finditer(r"\b" + re.escape(g) + r"\b", b.text):
                line = b.line + b.text[: m.start()].count("\n") if b.kind in SAMPLE_KINDS else b.line
                emit(b, line, g, [g], "resource", evidence="resource")
        # search parameters
        for m in re.finditer(r"(?:[?&`'\"\s(])((?:_[A-Za-z]+(?::[A-Za-z.]+)?|[a-z]+-[a-z]+|startIndex|excludeSAMHSA|includeTaxNumbers|cursor)(?:[:.][A-Za-z.]+)?)(?==|`|\b)", b.text):
            name = m.group(1)
            for variant in (name, name.split("=")[0]):
                if variant in idx.all_search:
                    res = [r for r, s in idx.search_params.items() if variant in s]
                    cands = [f"{r}?{variant}" for r in res if (not ctx or r in ctx)] or [f"{r}?{variant}" for r in res]
                    line = b.line + b.text[: m.start()].count("\n") if b.kind in SAMPLE_KINDS else b.line
                    emit(b, line, variant, cands, "search_param", len(cands) > 1, evidence="search_param")
                    break
        if b.kind in SAMPLE_KINDS:
            root_hint = b.resource_hint if b.resource_hint in RESOURCES else ""
            for off, key, parts, root in json_keys(b.text, root_hint):
                if key in ("resourceType",):
                    continue
                if root and root not in RESOURCES:
                    continue                      # e.g. a Bundle wrapper or a contained resource
                cands = idx.match_parts(parts, root)
                amb = len(cands) > 1
                ev = "json_path"
                if not cands and not root and len(parts) == 1 and (near or ctx):
                    cands, amb = idx.resolve_name(key, list(near) or ctx, hw)
                    ev = "named_in_context"
                emit(b, b.line + off, key, cands, "element", amb, evidence=ev)
            continue
        # prose / list / table
        text = b.text
        cells = [c.strip() for c in text.strip("|").split("|")] if b.kind == "table" else []

        def accept(cands: list[str], need_resources: set[str]) -> list[str]:
            return [c for c in cands if c.split(".")[0] in need_resources]

        # 1. full or relative dotted paths: always fine
        for tok in re.findall(r"\b(?:[A-Za-z]+)(?:\.[A-Za-z]+(?:\[x\])?)+\b", text):
            cands = idx.resolve_path(tok)
            emit(b, b.line, tok, cands, "element", len(cands) > 1, evidence="path")
        for tok in re.findall(r"`([^`]+)`", text):
            if "." in tok:
                cands = idx.resolve_path(tok)
                emit(b, b.line, tok, cands, "element", len(cands) > 1, evidence="path")
        # 2. field lists / tables: the resource (or the parent element) must be named in the heading or page title
        if b.kind in ("list_item", "table"):
            whole = text.strip().strip("`*_ ")
            names = [whole] if b.kind == "list_item" else [c.strip("`*_ ") for c in cells]
            for nm in names:
                if not (IDENT.fullmatch(nm or " ") and "." not in nm and nm[:1].islower()) or nm in GENERIC_WORDS:
                    continue
                cands, amb = idx.resolve_name(nm, ctx, hw)
                cands = accept(cands, set(ctx)) if ctx else []
                emit(b, b.line, nm, cands, "element", amb and len(cands) > 1,
                     evidence="field_list" if b.kind == "list_item" else "field_table")
        # 3. prose (and the words inside lists/tables): lowerCamel names or backticked unique words
        #    count only when their resource is named nearby
        toks: list[str] = []
        for tok in re.findall(r"`([^`]+)`", text):
            if "." in tok or not IDENT.fullmatch(tok) or not tok[:1].islower():
                continue
            if CAMEL.match(tok) or (tok.lower() not in COMMON_WORDS and len(idx.by_name.get(tok.lower(), [])) == 1):
                toks.append(tok)
        toks += [w for w in re.findall(r"\b[a-z]+(?:[A-Z][a-z0-9]*)+\b", text) if w not in GENERIC_WORDS]
        for w in dict.fromkeys(toks):
            cands, amb = idx.resolve_name(w, list(near) or ctx, hw, choice=False)
            cands = accept(cands, near) if near else []
            emit(b, b.line, w, cands, "element", amb and len(cands) > 1, evidence="named_in_context")
    return out
