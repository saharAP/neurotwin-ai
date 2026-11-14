"""Turn Europe PMC JATS XML into plain text the extractor (and quote check) can use.

Keeps the abstract, body sections with their titles, figure captions and table
contents (one row per line, cells separated by " | "). References, author
notes and front-matter metadata are dropped.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

SKIP = {"ref-list", "back", "fn-group", "ack", "xref"}


def _text(el: ET.Element) -> str:
    return " ".join(" ".join(el.itertext()).split())


def _walk(el: ET.Element, out: list[str], depth: int) -> None:
    tag = el.tag
    if tag in SKIP and tag != "xref":
        return
    if tag == "sec":
        title = el.find("title")
        if title is not None:
            out.append("\n" + "#" * min(depth + 2, 4) + " " + _text(title))
        for child in el:
            if child.tag != "title":
                _walk(child, out, depth + 1)
        return
    if tag == "p":
        out.append(_text(el))
        return
    if tag == "fig":
        label = el.find("label")
        cap = el.find("caption")
        out.append(f"[{_text(label) if label is not None else 'Figure'}] "
                   f"{_text(cap) if cap is not None else ''}")
        return
    if tag == "table-wrap":
        label = el.find("label")
        cap = el.find("caption")
        out.append(f"[{_text(label) if label is not None else 'Table'}] "
                   f"{_text(cap) if cap is not None else ''}")
        for row in el.iter("tr"):
            cells = [_text(c) for c in row if c.tag in {"td", "th"}]
            if any(cells):
                out.append(" | ".join(cells))
        foot = el.find("table-wrap-foot")
        if foot is not None:
            out.append(_text(foot))
        return
    for child in el:
        _walk(child, out, depth)


def jats_to_text(path: Path) -> str:
    root = ET.fromstring(path.read_bytes())
    out: list[str] = []
    title = root.find(".//article-meta/title-group/article-title")
    if title is not None:
        out.append("# " + _text(title))
    for abstract in root.findall(".//article-meta/abstract"):
        out.append("\n## Abstract")
        _walk(abstract, out, 1)
    body = root.find(".//body")
    if body is not None:
        _walk(body, out, 0)
    # Floating figures/tables sometimes sit outside <body>.
    floats = root.find(".//floats-group")
    if floats is not None:
        out.append("\n## Figures and tables")
        _walk(floats, out, 1)
    text = "\n".join(s for s in out if s.strip())
    return re.sub(r"\n{3,}", "\n\n", text)


def normalize(s: str) -> str:
    """For quote matching: case-folded, unified dashes/quotes/spaces, no spaces around symbols."""
    s = s.lower()
    s = s.translate(str.maketrans({"−": "-", "–": "-", "—": "-", "‐": "-",
                                   "‑": "-", "±": "+-", "‘": "'", "’": "'",
                                   "“": '"', "”": '"', " ": " ", " ": " ",
                                   " ": " ", "µ": "μ"}))
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*([=<>|,;:()\[\]/+-])\s*", r"\1", s)
    return s.strip()


def quote_in_text(quote: str, text_normalized: str) -> bool:
    q = normalize(quote).strip(" .\"'")
    if len(q) < 8:
        return False
    if q in text_normalized:
        return True
    # Allow an ellipsis joining two exact fragments.
    parts = [p.strip() for p in re.split(r"\.\.\.|…", q) if p.strip()]
    return len(parts) > 1 and all(len(p) >= 8 and p in text_normalized for p in parts)
