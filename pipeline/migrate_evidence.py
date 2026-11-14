"""Re-validate stored evidence rows against the current schema and rewrite them.

Run after a schema change:  python migrate_evidence.py [--dry-run]
Each row is loaded through schema.EvidenceRow, which applies the schema's own
normalization (canonical time units, lower-cased species). Values are never
converted. A row that no longer validates stops the run; nothing is written.
"""
from __future__ import annotations

import sys

from common import DATA, read_jsonl, write_jsonl
from schema import SCHEMA_VERSION, EvidenceRow, endpoint_key, now_utc, validate

ROWS_FILE = DATA / "evidence" / "evidence_rows.jsonl"


def migrate(row: dict) -> dict:
    new = {**row, "meta": dict(row["meta"]), "measurement": dict(row["measurement"])}
    if not new["measurement"].get("endpoint_normalized"):
        new["measurement"]["endpoint_normalized"] = endpoint_key(new["measurement"]["endpoint_original"])
    new["meta"]["schema_version"] = SCHEMA_VERSION
    out = EvidenceRow.model_validate(new).model_dump(mode="json")
    if out != row:
        out["meta"]["updated_at"] = now_utc()
    return out


def main() -> None:
    dry = "--dry-run" in sys.argv
    rows = list(read_jsonl(ROWS_FILE))
    bad = [(r["evidence_id"], errs) for r in rows
           if (errs := validate(EvidenceRow, {**r, "meta": {**r["meta"], "schema_version": SCHEMA_VERSION}}))]
    if bad:
        for eid, errs in bad:
            print(f"{eid}: {'; '.join(errs)}")
        sys.exit(f"{len(bad)} of {len(rows)} rows fail {SCHEMA_VERSION}; nothing written")
    out = [migrate(r) for r in rows]
    changed = sum(a != b for a, b in zip(rows, out))
    if not dry:
        write_jsonl(ROWS_FILE, out)
    print(f"{'would migrate' if dry else 'migrated'} {changed} of {len(rows)} rows to {SCHEMA_VERSION}")


if __name__ == "__main__":
    main()
