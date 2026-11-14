"""Shared config and helpers for the MVP v0 paper pipeline."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import unquote

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DISCOVERY_FILE = DATA / "discovery" / "open_posts.jsonl"
PAPERS_FILE = DATA / "papers" / "papers.jsonl"
CORPUS_FILE = DATA / "papers" / "corpus.jsonl"
FROZEN_SPLIT_FILE = DATA / "papers" / "frozen_split.json"
UNRESOLVED_FILE = DATA / "papers" / "unresolved.jsonl"
EXCLUSIONS_FILE = DATA / "papers" / "exclusions.jsonl"
FULLTEXT_DIR = DATA / "fulltext"  # gitignored: licensed full text stays local

USER_AGENT = "NeuroTwinAI-mvp0-research-pipeline/0.1"

# Which interventions the pipeline collects evidence for. Nothing below is specific to one
# compound: add an entry to config/interventions.json to cover another substance, or a
# non-substance setting such as sleep, exercise or an environmental exposure.
INTERVENTIONS_FILE = ROOT / "config" / "interventions.json"
_CONFIG = json.loads(INTERVENTIONS_FILE.read_text())
INTERVENTIONS: list[dict] = _CONFIG["interventions"]
OUTCOME_TERMS: dict[str, list[str]] = _CONFIG["outcome_terms"]
INTERVENTION_NAMES = [i["name"] for i in INTERVENTIONS]

# OPEN Foundation WordPress category IDs (from /wp-json/wp/v2/categories), for the
# interventions OPEN has a category for. Others are found by the literature search only.
SUBSTANCES = {i["open_category"]: i["name"] for i in INTERVENTIONS if i.get("open_category")}
THERAPEUTIC_AREAS = {
    36: "Depressive disorders",
    35: "Anxiety/PTSD",
    77: "Headache/pain/neurological",
}
# Second discovery path: neuron-level research often has no therapeutic tag.
DISCIPLINES = {67: "Neuroscience"}
NEUROSCIENCE_AREA = "Neurobiology (no therapeutic tag)"

EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"

_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT
_last_call: dict[str, float] = {}


def get(url: str, *, params: dict | None = None, min_interval: float = 0.5,
        retries: int = 3, timeout: float = 60) -> requests.Response:
    """GET with per-host politeness delay and simple retry on transient errors."""
    host = url.split("/")[2]
    for attempt in range(retries):
        wait = min_interval - (time.monotonic() - _last_call.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        _last_call[host] = time.monotonic()
        try:
            resp = _session.get(url, params=params, timeout=timeout)
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
            continue
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
            time.sleep(2 ** (attempt + 1))
            continue
        return resp
    raise RuntimeError("unreachable")


def read_jsonl(path: Path) -> Iterator[dict]:
    with path.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
    return n


# --- identifier extraction from links -------------------------------------

_DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s?#\"'<>]+)", re.I)
_PMC_RE = re.compile(r"\b(PMC\d+)\b", re.I)
_PUBMED_RE = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)|ncbi\.nlm\.nih\.gov/pubmed/(\d+)")
_NATURE_RE = re.compile(r"nature\.com/articles/([a-z0-9.\-]+)", re.I)


def clean_doi(doi: str) -> str:
    doi = unquote(doi).strip().rstrip(".,;)")
    # Strip trailing landing-page path segments publishers append after the DOI.
    doi = re.sub(r"/(abstract|full|pdf|epdf|html|fulltext)$", "", doi, flags=re.I)
    doi = re.sub(r"\.(pdf|html)$", "", doi, flags=re.I)
    return doi.lower()


def identifier_from_url(url: str) -> dict | None:
    """Return {'doi'|'pmcid'|'pmid': value} for scholarly links, else None."""
    if m := _PMC_RE.search(url):
        return {"pmcid": m.group(1).upper()}
    if m := _PUBMED_RE.search(url):
        return {"pmid": m.group(1) or m.group(2)}
    if m := _DOI_RE.search(unquote(url)):
        return {"doi": clean_doi(m.group(1))}
    if m := _NATURE_RE.search(url):
        return {"doi": clean_doi("10.1038/" + m.group(1))}
    return None


def strip_tags(html: str) -> str:
    import html as _html
    text = re.sub(r"<[^>]+>", " ", _html.unescape(html))  # Europe PMC titles can be entity-escaped
    for ent, ch in (("&amp;", "&"), ("&#8211;", "-"), ("&#8217;", "'"),
                    ("&#8220;", '"'), ("&#8221;", '"'), ("&nbsp;", " ")):
        text = text.replace(ent, ch)
    return re.sub(r"\s+", " ", text).strip()
