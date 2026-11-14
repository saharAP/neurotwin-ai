"""Step 3: choose the extraction corpus from Publication records.

Deterministic filters only; screening that needs judgment ("does this paper
report a measured outcome?") is left to the later LLM screening step.
Criteria never look at effect direction. Every excluded publication is written
to exclusions.jsonl with its reason so the selection can be audited.
"""
from __future__ import annotations

import json
from collections import Counter

from common import (CORPUS_FILE, EXCLUSIONS_FILE, FROZEN_SPLIT_FILE, INTERVENTIONS, PAPERS_FILE,
                    read_jsonl, write_jsonl)
from schema import PIPELINE_VERSION, now_utc

MAX_PAPERS = 50  # general cap (raised from 40 on 2026-11-08 when PubMed search was added)
# An intervention with `corpus_cap` in config/interventions.json gets that many places of its
# own on top of the general cap, so adding an intervention never pushes existing papers out.
OWN_CAP = {i["name"]: i["corpus_cap"] for i in INTERVENTIONS if i.get("corpus_cap")}
DEV_PAPERS = 5

# A discovery tag accepts the intervention it names, plus any listed under
# `open_tag_also_covers` in config/interventions.json (OPEN's "DMT" category also holds
# 5-MeO-DMT papers, because its own 5-MeO-DMT category has only a few posts).
TAG_COVERS = {i["name"]: {i["name"], *i.get("open_tag_also_covers", [])} for i in INTERVENTIONS}


def corpus_substances(p: dict) -> list[str]:
    """Substances named in the paper itself that some OPEN tag on it covers."""
    accepted = set().union(*(TAG_COVERS.get(t, {t}) for t in
                             p["extended"]["discovery"]["open_substance_tags"]))
    return sorted(set(p["extended"]["substances_in_paper"]) & accepted)


# (code, description) checked in order; first failing criterion is recorded.
CRITERIA = [
    ("retracted", "publication is retracted or has an expression of concern",
     lambda p: not (p["is_retracted"] or p["extended"]["concerns"])),
    ("review_discovery_only", "review: used for discovery, not measurement",
     lambda p: p["source_role"] == "primary_measurement"),
    ("non_research_type", "editorial, comment, letter or similar",
     lambda p: p["publication_type"] != "editorial_or_comment"),
    ("preprint", "not peer reviewed",
     lambda p: p["peer_review_status"] == "peer_reviewed"),
    ("no_open_full_text", "no open-access full text in Europe PMC",
     lambda p: p["full_text_access"] == "open_full_text"),
    ("substance_tag_mismatch", "OPEN substance tag not found in paper title/abstract",
     lambda p: bool(corpus_substances(p))),
]


def main() -> None:
    pubs = list(read_jsonl(PAPERS_FILE))
    eligible, exclusions = [], []
    for p in pubs:
        failed = next(((code, desc) for code, desc, ok in CRITERIA if not ok(p)), None)
        if failed:
            exclusions.append({"publication_id": p["publication_id"], "doi": p["doi"],
                               "title": p["title"], "exclusion_code": failed[0],
                               "exclusion_reason": failed[1], "stage": "deterministic_filter",
                               "decided_at": now_utc(), "extractor_version": PIPELINE_VERSION})
        else:
            eligible.append(p)

    # Papers already in the frozen split keep their place and split, so widening
    # discovery never rotates dev or held-out papers out. New papers are appended
    # as held-out in a fixed, effect-blind order (publication_id is a hash).
    frozen = (json.loads(FROZEN_SPLIT_FILE.read_text())["papers"]
              if FROZEN_SPLIT_FILE.exists() else {})
    eligible.sort(key=lambda p: p["publication_id"])
    kept = [p for p in eligible if p["publication_id"] in frozen]
    lost = set(frozen) - {p["publication_id"] for p in kept}
    if lost:
        print(f"  WARNING: {len(lost)} frozen papers are no longer eligible: {sorted(lost)}")
    # New papers from the neuron-level literature search come first (this stage's goal),
    # then other new papers; within each group the order is the effect-blind hash.
    new = sorted((p for p in eligible if p["publication_id"] not in frozen),
                 key=lambda p: (not any(v.get("source") == "europepmc_search"
                                        for v in p["extended"]["discovery"]["found_via"]),
                                p["publication_id"]))
    # Interventions with their own cap fill their own places, in the same effect-blind order.
    reserved: list[dict] = []
    for name, cap in OWN_CAP.items():
        mine = [p for p in new if name in corpus_substances(p) and p not in reserved]
        have = sum(name in corpus_substances(p) for p in kept)
        reserved += mine[:max(0, cap - have)]
    new = [p for p in new if not any(n in corpus_substances(p) for n in OWN_CAP)]
    room = max(0, MAX_PAPERS - sum(not any(n in corpus_substances(p) for n in OWN_CAP) for p in kept))
    own_all = [p for p in eligible if p["publication_id"] not in frozen
               and any(n in corpus_substances(p) for n in OWN_CAP) and p not in reserved]
    for p in new[room:] + own_all:
        exclusions.append({"publication_id": p["publication_id"], "doi": p["doi"],
                           "title": p["title"], "exclusion_code": "over_cap",
                           "exclusion_reason": "beyond the corpus cap for this intervention",
                           "stage": "cap", "decided_at": now_utc(),
                           "extractor_version": PIPELINE_VERSION})

    rows = []
    for i, p in enumerate(kept + new[:room] + reserved):
        ext = p["extended"]
        pid = p["publication_id"]
        split = frozen.get(pid) or ("dev" if not frozen and i < DEV_PAPERS else "heldout")
        ext["corpus"] = {
            "substances": corpus_substances(p),
            "therapeutic_areas": ext["discovery"]["open_therapeutic_tags"],
            "split": split,
            "added": "frozen" if pid in frozen else "appended",
            "screening_status": "pending_llm_screen",
        }
        rows.append(p)
    write_jsonl(CORPUS_FILE, rows)
    write_jsonl(EXCLUSIONS_FILE, exclusions)

    print(f"publications: {len(pubs)}")
    for code, n in Counter(e["exclusion_code"] for e in exclusions).most_common():
        print(f"  excluded - {code}: {n}")
    splits = Counter(r["extended"]["corpus"]["split"] for r in rows)
    print(f"selected: {len(rows)} ({splits['dev']} dev, {splits['heldout']} held-out; "
          f"{len(kept)} frozen, {len(rows) - len(kept)} appended)")
    cells = Counter((s, a) for r in rows for s in r["extended"]["corpus"]["substances"]
                     for a in r["extended"]["corpus"]["therapeutic_areas"])
    for (s, a), n in sorted(cells.items()):
        print(f"  {s} x {a}: {n}")


if __name__ == "__main__":
    main()
