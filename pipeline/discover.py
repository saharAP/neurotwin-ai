"""Step 1: discover candidate papers through OPEN Foundation posts.

OPEN is used only to find reference papers. We read each post in memory to
pull out scholarly links, and store only a discovery log: post URL, title,
date, categories, and the paper identifiers it points to. No OPEN text is kept.
"""
from __future__ import annotations

import re

from common import (DISCIPLINES, DISCOVERY_FILE, NEUROSCIENCE_AREA, SUBSTANCES,
                    THERAPEUTIC_AREAS, get,
                    identifier_from_url, strip_tags, write_jsonl)

WP_POSTS = "https://open-foundation.org/wp-json/wp/v2/posts"
PAPERS_CATEGORY = 16  # OPEN's "Papers" database entries (one paper per post)


def fetch_posts(category_id: int) -> list[dict]:
    posts, page = [], 1
    while True:
        resp = get(WP_POSTS, params={
            "categories": category_id, "per_page": 100, "page": page,
            "_fields": "id,link,date,title,categories,content",
        })
        if resp.status_code == 400:  # past the last page
            break
        resp.raise_for_status()
        batch = resp.json()
        posts.extend(batch)
        if page >= int(resp.headers.get("X-WP-TotalPages", page)):
            break
        page += 1
    return posts


def main() -> None:
    by_id: dict[int, dict] = {}
    for cat in SUBSTANCES:
        for post in fetch_posts(cat):
            by_id[post["id"]] = post
    print(f"fetched {len(by_id)} posts across {len(SUBSTANCES)} substances")

    rows = []
    for post in sorted(by_id.values(), key=lambda p: p["id"]):
        cats = set(post["categories"])
        substances = sorted(SUBSTANCES[c] for c in cats & SUBSTANCES.keys())
        areas = sorted(THERAPEUTIC_AREAS[c] for c in cats & THERAPEUTIC_AREAS.keys())
        disciplines = sorted(DISCIPLINES[c] for c in cats & DISCIPLINES.keys())
        if areas:
            path = "therapeutic_tag"
        elif "Neuroscience" in disciplines:
            path, areas = "neuroscience_tag", [NEUROSCIENCE_AREA]
        else:
            path = None
        links = sorted(set(re.findall(r'href="([^"]+)"', post["content"]["rendered"])))
        refs, seen = [], set()
        for url in links:
            ident = identifier_from_url(url)
            if ident and (key := tuple(ident.items())) not in seen:
                seen.add(key)
                refs.append({**ident, "url": url})
        rows.append({
            "post_id": post["id"],
            "post_url": post["link"],
            "post_title": strip_tags(post["title"]["rendered"]),
            "post_date": post["date"][:10],
            "post_kind": "paper_entry" if PAPERS_CATEGORY in cats else "article",
            "substances": substances,
            "therapeutic_areas": areas,
            "disciplines": disciplines,
            "discovery_path": path,
            "in_scope": bool(substances and path),
            "references": refs,
        })

    n = write_jsonl(DISCOVERY_FILE, rows)
    in_scope = [r for r in rows if r["in_scope"]]
    print(f"wrote {n} posts -> {DISCOVERY_FILE.relative_to(DISCOVERY_FILE.parents[2])}")
    print(f"in scope: {len(in_scope)} (therapeutic tag "
          f"{sum(r['discovery_path'] == 'therapeutic_tag' for r in in_scope)}, neuroscience only "
          f"{sum(r['discovery_path'] == 'neuroscience_tag' for r in in_scope)})")
    print(f"  with >=1 scholarly link: {sum(1 for r in in_scope if r['references'])}")
    print(f"  without links (title-only): {sum(1 for r in in_scope if not r['references'])}")


if __name__ == "__main__":
    main()
