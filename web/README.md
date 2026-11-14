# MVP v0 web UI: Neuron Outcome Atlas

An early, read-only Next.js prototype over the pipeline output in `../data`. It is not yet ready for demos: the data is a small first corpus and nothing has been expert-reviewed. [docs/MVP_V0.md](../docs/MVP_V0.md) describes the plan.

| Route | Screen |
|---|---|
| `/` | Atlas: one row per neuron outcome, one column per intervention; each cell counts the studies and measurements |
| `/outcomes/[id]` | One outcome: filters, each measurement against its own study's control, a schematic of one study, and the measurement table with source quotes |
| `/studies`, `/studies/[id]` | Study list, and everything one paper measured |
| `/about` | How the corpus was selected and the extraction status, counted from the data |
| `/api/export?ids=…&format=csv\|json\|md` | Export with citations and limitations |

```bash
npm install
npm run dev        # http://localhost:3000
```

**Environment variables (all optional):**
- `DATA_DIR`: the pipeline data folder. Defaults to `../data`.
- `EVIDENCE_FILE`: the evidence-row JSONL. Defaults to `$DATA_DIR/evidence/evidence_rows.jsonl`. `pipeline/extract.py` writes this file.
- `EVIDENCE_FIXTURE=1`: shows a red "test fixture" banner on every page and marks exports. Use it whenever `EVIDENCE_FILE` points at made-up test rows. Never put fixture rows in `data/`.

**Types:** `lib/types.ts` mirrors `pipeline/schema.py`; the Python file is the source of truth.

