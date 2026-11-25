"""2E. MCP server. Serves ONLY from publish/ and reports/. Four read-only tools."""
from __future__ import annotations
import json, re
from pathlib import Path


class Store:
    def __init__(self, publish_dir: Path, reports_dir: Path):
        self.publish = Path(publish_dir).resolve()
        self.reports = Path(reports_dir).resolve()

    def _safe(self, base: Path, rel: str) -> Path:
        p = (base / rel).resolve()
        if base not in p.parents and p != base:
            raise ValueError("path outside the served folders")
        return p

    def manifest(self) -> dict:
        return json.loads(self._safe(self.publish, "manifest.json").read_text())

    def search_docs(self, query: str, api_version: str = "2") -> list[dict]:
        words = [w.lower() for w in re.findall(r"\w+", query)]
        hits = []
        for pg in self.manifest()["pages"]:
            if api_version and api_version.strip().lstrip("vV")[:1] != pg["api_version"][:1]:
                continue
            text = self._safe(self.publish, f"pages/{pg['id']}.md").read_text(encoding="utf-8").lower()
            score = sum(text.count(w) for w in words)
            if words and all(w in text for w in words):
                score += 10
            if score:
                i = text.find(words[0]) if words else 0
                hits.append({"id": pg["id"], "title": pg["title"], "score": score,
                             "snippet": text[max(0, i - 60):i + 140].replace("\n", " "),
                             "status": "verified" if not pg["open_findings"] else "needs_review"})
        return sorted(hits, key=lambda h: -h["score"])[:10]

    def get_page(self, page_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", page_id):
            raise ValueError("bad page id")
        return self._safe(self.publish, f"pages/{page_id}.md").read_text(encoding="utf-8")

    def get_drift_report(self) -> dict:
        d = json.loads(self._safe(self.reports, "drift-report.json").read_text())
        return {"summary": d["summary"], "findings": [
            {k: f[k] for k in ("id", "label", "confidence", "v1_element", "v2_element", "detail")}
            for f in d["findings"][:200]]}

    def get_change(self, element: str) -> dict:
        d = json.loads(self._safe(self.reports, "drift-report.json").read_text())
        e = element.lower()
        ch = [c for c in d["spec_changes"] if e in (c["v1_path"] + " " + c["v2_path"]).lower()]
        fi = [f for f in d["findings"] if e in (f["v1_element"] + " " + f["v2_element"]).lower()]
        return {"element": element, "spec_changes": ch[:20], "findings": fi[:20]}


def build_server(publish_dir: Path, reports_dir: Path):
    from mcp.server.mcpserver import MCPServer
    store = Store(publish_dir, reports_dir)
    mcp = MCPServer("truthlayer")

    @mcp.tool()
    def search_docs(query: str, api_version: str = "2") -> list[dict]:
        """Search the verified documentation pages. api_version: '2' (default)."""
        return store.search_docs(query, api_version)

    @mcp.tool()
    def get_page(id: str) -> str:
        """Return one published page (Markdown with front matter) by its id."""
        return store.get_page(id)

    @mcp.tool()
    def get_drift_report() -> dict:
        """Summary and findings of the latest drift check."""
        return store.get_drift_report()

    @mcp.tool()
    def get_change(element: str) -> dict:
        """What changed between v1 and v2 for an element name or path, and any doc findings."""
        return store.get_change(element)

    return mcp
