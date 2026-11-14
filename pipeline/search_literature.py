"""Step 1b: find neuron-level primary studies directly in PubMed (via Europe PMC).

OPEN Foundation coverage is mostly clinical. This search adds open-access PubMed
papers where a configured intervention is in the title and a neuroplasticity term is in
the title or abstract. Results are stored as references only (identifiers, the
query and the search date); resolve.py turns them into Publication records and
select_corpus.py applies the same filters and cap as for OPEN-found papers.

The query never mentions results or effect direction, so selection stays
effect-blind. Search results drift over time, so the date is recorded and the
selected papers are frozen in frozen_split.json once chosen.
"""
from __future__ import annotations

from common import DATA, EUROPE_PMC, INTERVENTIONS, OUTCOME_TERMS, get, write_jsonl
from schema import now_utc

SEARCH_FILE = DATA / "discovery" / "literature_search.jsonl"

# One query per intervention in config/interventions.json: its search terms in the title,
# and an outcome term in the title or abstract. To cover another substance, or sleep,
# exercise or an environmental setting, add it to that file; nothing here names a compound.
_any = " OR ".join
FILTERS = (
    f'(ABSTRACT:({_any(OUTCOME_TERMS["abstract"])}) '
    f'OR TITLE:({_any(OUTCOME_TERMS["title"])})) '
    'AND OPEN_ACCESS:y AND SRC:MED AND IN_EPMC:y '
    'NOT PUB_TYPE:"Review" NOT PUB_TYPE:"review-article" NOT PUB_TYPE:"Editorial" '
    'NOT PUB_TYPE:"Comment" NOT PUB_TYPE:"Letter"'
)
MAX_RESULTS = 300  # per intervention


def query_for(intervention: dict) -> str:
    return f'TITLE:({_any(intervention["search_terms"])}) AND {FILTERS}'


def search(intervention: dict) -> list[dict]:
    query, rows, cursor = query_for(intervention), [], "*"
    while len(rows) < MAX_RESULTS:
        resp = get(f"{EUROPE_PMC}/search", params={
            "query": query, "format": "json", "resultType": "lite",
            "pageSize": 100, "cursorMark": cursor})
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("resultList", {}).get("result", [])
        if not batch:
            break
        for r in batch:
            ident = ({"pmcid": r["pmcid"]} if r.get("pmcid") else
                     {"doi": r["doi"].lower()} if r.get("doi") else {"pmid": r.get("pmid")})
            rows.append({"reference": ident, "intervention": intervention["name"], "query": query,
                         "searched_at": now_utc(), "source": "europepmc_search",
                         "hit_count": data.get("hitCount")})
        nxt = data.get("nextCursorMark")
        if not nxt or nxt == cursor:
            break
        cursor = nxt
    return rows[:MAX_RESULTS]


def main() -> None:
    rows = []
    for intervention in INTERVENTIONS:
        found = search(intervention)
        rows += found
        print(f"  {intervention['name']}: {found[0]['hit_count'] if found else 0} hits, kept {len(found)}")
    n = write_jsonl(SEARCH_FILE, rows)
    print(f"literature search: {n} references -> {SEARCH_FILE.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
