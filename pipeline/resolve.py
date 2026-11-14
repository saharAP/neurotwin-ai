"""Step 2: resolve in-scope references to Publication records (DATA_STRATEGY §4).

Each reference (DOI / PMID / PMCID from a post link) is looked up in Europe PMC.
Paper-entry posts without links fall back to an exact-title search. Anything
that cannot be matched goes to unresolved.jsonl with a §3 missing_reason
rather than being guessed.
"""
from __future__ import annotations

import re
from collections import defaultdict

from common import (DATA, DISCOVERY_FILE, EUROPE_PMC, INTERVENTIONS, PAPERS_FILE,
                    UNRESOLVED_FILE, get,
                    read_jsonl, strip_tags, write_jsonl)
from schema import (PIPELINE_VERSION, SCHEMA_VERSION, Publication, now_utc,
                    stable_id, validate)

# OPEN tags posts broadly (e.g. an MDMA trial tagged Psilocybin), so the
# substance is re-derived from the paper's own title + abstract. Only the
# matched labels are stored, never the abstract text.
# Patterns come from config/interventions.json and are tried in the order listed there.
# Each match is blanked out before the next pattern runs, so a specific name listed first
# (5-MeO-DMT) is never counted again under a name it contains (DMT).
INTERVENTION_PATTERNS = [(i["name"], re.compile(i["match"], re.I)) for i in INTERVENTIONS]
SEARCH_FILE = DATA / "discovery" / "literature_search.jsonl"
LIT_AREA = "Neuroplasticity (PubMed search)"
RETRACTION_NOTICES = {"retraction in", "retracted and republished in",
                      "expression of concern in"}
CORRECTION_NOTICES = {"erratum in", "corrected and republished in", "update in"}


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_tags(t).lower()).strip()


def epmc_search(query: str) -> list[dict]:
    resp = get(f"{EUROPE_PMC}/search", params={
        "query": query, "format": "json", "resultType": "core", "pageSize": 5})
    resp.raise_for_status()
    return resp.json().get("resultList", {}).get("result", [])


def lookup(ref: dict) -> dict | None:
    if "doi" in ref:
        hits = epmc_search(f'DOI:"{ref["doi"]}"')
    elif "pmcid" in ref:
        hits = epmc_search(f'PMCID:{ref["pmcid"]}')
    else:
        hits = epmc_search(f'EXT_ID:{ref["pmid"]} AND SRC:MED')
    return hits[0] if hits else None


def lookup_title(title: str) -> dict | None:
    q = re.sub(r'["()]', " ", title)
    for hit in epmc_search(f'TITLE:"{q}"'):
        if norm_title(hit.get("title", "")) == norm_title(title):
            return hit
    return None


# --- §4 field mapping ---------------------------------------------------------

def publication_type(pub_types: set[str], source: str) -> str:
    if source == "PPR" or "preprint" in pub_types:
        return "other"  # preprint status lives in peer_review_status
    if pub_types & {"systematic review", "systematic-review", "meta-analysis"}:
        return "systematic_review"
    if pub_types & {"review", "review-article"}:
        return "narrative_review"
    if pub_types & {"editorial", "comment", "letter", "news", "discussion"}:
        return "editorial_or_comment"
    if pub_types & {"case reports", "case-report"}:
        return "case_report"
    if any("clinical trial" in t or t == "randomized controlled trial" for t in pub_types):
        return "clinical_trial"
    if "observational study" in pub_types:
        return "observational_study"
    # Generic "journal article"/"research-article": the design is not knowable
    # from metadata; LLM screening assigns it. Not labeled experimental here.
    return "other"


def source_role(pub_type: str) -> str:
    return ("review_discovery" if pub_type in {"systematic_review", "narrative_review"}
            else "primary_measurement")


def authors(hit: dict) -> list[dict]:
    out = []
    for a in hit.get("authorList", {}).get("author", []):
        aid = a.get("authorId") or {}
        out.append({
            "full_name": a.get("fullName") or a.get("collectiveName"),
            "last_name": a.get("lastName"),
            "first_name": a.get("firstName"),
            "orcid": aid.get("value") if aid.get("type") == "ORCID" else None,
            "affiliations": [x["affiliation"] for x in
                             a.get("authorAffiliationDetailsList", {}).get("authorAffiliation", [])
                             if x.get("affiliation")],
        })
    return out


def version_status(hit: dict, pub_types: set[str]) -> dict:
    notices = hit.get("commentCorrectionList", {}).get("commentCorrection", [])
    retractions = [n for n in notices if n.get("type", "").lower() in RETRACTION_NOTICES]
    corrections = [n for n in notices if n.get("type", "").lower() in CORRECTION_NOTICES]
    return {
        "is_retracted": "retracted publication" in pub_types or any(
            n["type"].lower().startswith("retraction") for n in retractions),
        "concerns": [{"type": n["type"], "id": n.get("id"), "source": n.get("source")}
                     for n in retractions],
        "corrections": [{"type": n["type"], "id": n.get("id"), "source": n.get("source")}
                        for n in corrections],
    }


def license_metadata(raw: str | None) -> str | None:
    """Europe PMC gives e.g. 'cc by' without version; refined from XML at fetch."""
    if not raw:
        return None
    return {"cc by": "CC-BY", "cc by-nc": "CC-BY-NC", "cc by-nc-nd": "CC-BY-NC-ND",
            "cc by-nc-sa": "CC-BY-NC-SA", "cc by-nd": "CC-BY-ND", "cc by-sa": "CC-BY-SA",
            "cc0": "CC0-1.0"}.get(raw.lower(), f"LicenseRef-{raw.replace(' ', '-')}")


def substances_mentioned(hit: dict) -> list[str]:
    text = strip_tags(hit.get("title", "") + " " + hit.get("abstractText", ""))
    found = set()
    for name, pattern in INTERVENTION_PATTERNS:
        if pattern.search(text):
            found.add(name)
            text = pattern.sub(" ", text)
    return sorted(found)


def publication_record(hit: dict, created_at: str | None) -> dict:
    """Core Publication (schema.Publication) + non-core §4 fields in `extended`."""
    pub_types = {t.lower() for t in hit.get("pubTypeList", {}).get("pubType", [])}
    ptype = publication_type(pub_types, hit.get("source", ""))
    doi = (hit.get("doi") or "").lower() or None
    key = doi or hit.get("pmcid") or f"MED:{hit.get('pmid')}"
    open_text = hit.get("isOpenAccess") == "Y" and bool(hit.get("pmcid"))
    version = version_status(hit, pub_types)
    grants = [{"agency": g.get("agency"), "grant_id": g.get("grantId")}
              for g in hit.get("grantsList", {}).get("grant", [])]
    ts = now_utc()
    rec = {
        "meta": {"schema_version": SCHEMA_VERSION, "pipeline_version": PIPELINE_VERSION,
                 "created_at": created_at or ts, "updated_at": ts,
                 "curation_status": "raw", "reviewer_id": None, "reviewed_at": None},
        "publication_id": stable_id("pub", key),
        "doi": doi,
        "pmid": hit.get("pmid"),
        "pmcid": hit.get("pmcid"),
        "title": strip_tags(hit.get("title", "")),
        "year": int(hit["pubYear"]) if hit.get("pubYear") else None,
        "journal": hit.get("journalInfo", {}).get("journal", {}).get("title")
                   or hit.get("bookOrReportDetails", {}).get("publisher"),
        "publication_type": ptype,
        "peer_review_status": "preprint" if (hit.get("source") == "PPR" or "preprint" in pub_types) else (
            "peer_reviewed" if hit.get("source") == "MED" else "unknown"),
        "is_retracted": version["is_retracted"],
        "license": license_metadata(hit.get("license")),
        "full_text_access": "open_full_text" if open_text else (
            "abstract" if hit.get("abstractText") else "unavailable"),
        "source_role": source_role(ptype),
        "extended": {
            "authors": authors(hit),
            "publication_date": hit.get("firstPublicationDate"),
            "url": f"https://doi.org/{doi}" if doi else
                   f"https://europepmc.org/article/{hit.get('source')}/{hit.get('id')}",
            "concerns": version["concerns"],
            "corrections": version["corrections"],
            "funding": grants or None,
            "conflicts_of_interest": None,   # from full text at fetch
            "dataset_links": None,           # from full text at fetch
            "source_publication_types": sorted(pub_types),
            "substances_in_paper": substances_mentioned(hit),
        },
    }
    rec["missing_reasons"] = {f: "not_reported" for f in Publication.NULLABLE_CORE
                              if rec[f] is None}
    return rec


def main() -> None:
    posts = [p for p in read_jsonl(DISCOVERY_FILE) if p["in_scope"]]
    previous = ({r["publication_id"]: r.get("meta", r).get("created_at")
                 for r in read_jsonl(PAPERS_FILE) if "publication_id" in r}
                if PAPERS_FILE.exists() else {})
    hits: dict[str, dict] = {}
    found_via: dict[str, list] = defaultdict(list)
    unresolved = []

    for i, post in enumerate(posts, 1):
        cell = {"post_url": post["post_url"], "substances": post["substances"],
                "therapeutic_areas": post["therapeutic_areas"]}
        matched = []
        for ref in post["references"]:
            if hit := lookup(ref):
                matched.append((hit, "identifier_link"))
            else:
                unresolved.append({**cell, "reference": ref, "missing_reason": "not_accessible",
                                   "detail": "identifier not found in Europe PMC"})
        if not post["references"]:
            if post["post_kind"] == "paper_entry" and (hit := lookup_title(post["post_title"])):
                matched.append((hit, "exact_title"))
            else:
                unresolved.append({
                    **cell, "reference": {"title": post["post_title"]},
                    "missing_reason": "pending_review",
                    "detail": ("no link and no exact title match" if post["post_kind"] == "paper_entry"
                               else "article without links; needs LLM resolution")})
        for hit, method in matched:
            doi = (hit.get("doi") or "").lower() or None
            pid = stable_id("pub", doi or hit.get("pmcid") or f"MED:{hit.get('pmid')}")
            hits.setdefault(pid, hit)
            found_via[pid].append({**cell, "match": method})
        if i % 25 == 0:
            print(f"  {i}/{len(posts)} posts, {len(hits)} papers so far")

    # Second source: direct PubMed/Europe PMC search (search_literature.py). These papers
    # have no OPEN tags, so their substance tags come from the paper's own title/abstract.
    search_refs = list(read_jsonl(SEARCH_FILE)) if SEARCH_FILE.exists() else []
    for s in search_refs:
        hit = lookup(s["reference"])
        if not hit:
            unresolved.append({"post_url": None, "substances": [], "therapeutic_areas": [LIT_AREA],
                               "reference": s["reference"], "missing_reason": "not_accessible",
                               "detail": "search hit not found in Europe PMC"})
            continue
        doi = (hit.get("doi") or "").lower() or None
        pid = stable_id("pub", doi or hit.get("pmcid") or f"MED:{hit.get('pmid')}")
        hits.setdefault(pid, hit)
        found_via[pid].append({"post_url": None, "source": "europepmc_search",
                               # Tag only the intervention the search was for, and only if the
                               # paper itself names it (older search files have no intervention).
                               "substances": [x for x in substances_mentioned(hit)
                                              if x == s.get("intervention", x)],
                               "therapeutic_areas": [LIT_AREA], "match": "literature_search"})
    print(f"  literature search: {len(search_refs)} references")

    rows, invalid = [], 0
    for pid, hit in sorted(hits.items()):
        rec = publication_record(hit, previous.get(pid))
        via = found_via[pid]
        rec["extended"]["discovery"] = {
            "found_via": via,
            "open_substance_tags": sorted({s for v in via for s in v["substances"]}),
            "open_therapeutic_tags": sorted({a for v in via for a in v["therapeutic_areas"]}),
        }
        if errs := validate(Publication, rec):
            invalid += 1
            print(f"  SCHEMA {pid}: {errs}")
        rows.append(rec)

    write_jsonl(PAPERS_FILE, rows)
    write_jsonl(UNRESOLVED_FILE, unresolved)
    primary = [r for r in rows if r["source_role"] == "primary_measurement"]
    print(f"publications: {len(rows)} (primary {len(primary)}, reviews {len(rows) - len(primary)}), "
          f"schema errors: {invalid}")
    print(f"  retracted: {sum(r['is_retracted'] for r in rows)}, "
          f"with corrections: {sum(bool(r['extended']['corrections']) for r in rows)}")
    print(f"unresolved references: {len(unresolved)}")


if __name__ == "__main__":
    main()
