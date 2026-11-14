# MVP v0 paper pipeline

Builds the fixed paper corpus described in [docs/MVP_V0.md](../docs/MVP_V0.md). NeuroTwin's subject is how substances and environmental settings change brain function. Which interventions are collected is set in [config/interventions.json](../config/interventions.json): add an entry (name, type, search terms, match pattern) to cover another substance, or sleep, exercise or an environmental setting. The three compounds there now are only the first test corpus.
OPEN Foundation is used only to find reference papers. All metadata comes from Europe PMC.

```bash
python3 -m venv .venv && .venv/bin/pip install -r pipeline/requirements.txt
cd pipeline
../.venv/bin/python discover.py        # OPEN posts -> data/discovery/open_posts.jsonl
../.venv/bin/python search_literature.py  # Europe PMC search -> data/discovery/literature_search.jsonl
../.venv/bin/python resolve.py         # Europe PMC lookup -> data/papers/papers.jsonl
../.venv/bin/python select_corpus.py   # filters + dev/held-out split -> data/papers/corpus.jsonl
../.venv/bin/python fetch_fulltext.py  # open-access JATS XML -> data/fulltext/ (gitignored)
../.venv/bin/python extract.py --split dev   # Claude API extraction -> data/evidence/ (needs a key)
```

| Step | What it does |
|---|---|
| `discover.py` | Lists OPEN posts for the interventions that have an OPEN category in the config (WordPress REST API). Keeps posts that also have a therapeutic tag (depression, anxiety/PTSD, neurological), or that are tagged Neuroscience with no therapeutic tag (mostly cell, animal and imaging studies). Stores only the post URL, title, date, tags and paper links. No OPEN text is stored. |
| `search_literature.py` | Runs one Europe PMC search per intervention in the config: its search terms in the title, and an outcome term in the title or abstract. Open-access primary studies only. Stores identifiers, the query and the search date. |
| `resolve.py` | Looks up each DOI, PMID or PMCID in Europe PMC. Paper posts with no link fall back to an exact title match. Marks reviews as `review_discovery`. Re-checks that the substance named in OPEN's tag appears in the paper's own title or abstract. Anything it can't match is kept as `unresolved`, not guessed. |
| `select_corpus.py` | Removes reviews, editorials, letters, comments, papers without open-access full text, and papers whose substance tag doesn't match. A substance counts only if the paper names it and an OPEN tag covers it; OPEN's DMT tag also covers 5-MeO-DMT, because OPEN files most 5-MeO-DMT papers under DMT. Takes at most 50 papers, plus the places an intervention reserves with `corpus_cap` in the config (exercise has 15). Papers in `frozen_split.json` keep their place and split; new papers are appended as `heldout` in a fixed, effect-blind order (sorted by hash). |
| `fetch_fulltext.py` | Downloads Europe PMC `fullTextXML` and supplement archives, and records each file's SHA-256 hash and the license stated in the XML. A failed or timed-out download is recorded and retried on the next run. Run it again after `select_corpus.py`, which rewrites `corpus.jsonl`. |

## Core schema

[schema.py](schema.py) is the single source of truth for v0 records. It is a lean, validated subset of [docs/DATA_STRATEGY.md](../docs/DATA_STRATEGY.md):

- **`Publication`** has 13 core fields. Every step validates it.
- **`EvidenceRow`** is one flat row per measurement: experiment, arm, measurement and source anchors, plus an optional `ClinicalExtension` (rating scale, response/remission, adverse events, blinding) for human studies or `PreclinicalExtension` (cell type, brain region, culture or animal age, sex, strain, and mechanism probes such as antagonists or knockdowns) for cell and animal studies.
- **Empty core fields** must have a `missing_reason`. Every other dictionary field goes in `extended`, which is not validated.
- **Built-in rules:** a dose needs its original unit; a confidence interval needs both bounds; clinical endpoints need a human study design. During extraction, code checks each anchor's quote against the full text (`jats_text.py`) and sets `quote_verified`; rows with no verified quote are rejected.

- **Any intervention (core-0.4.0):** each arm has an `intervention_type`; a non-substance arm has no dose and must give its protocol in `regimen`.
- **Normalized on load (core-0.3.0):** `time_unit` must be one of seconds, minutes, hours, days, weeks, months or years (variants such as `day` or `hr` are mapped, anything else is rejected); `endpoint_normalized` is a required snake_case key; `species` is lower-cased. Values are never converted.

Regenerate the JSON Schema with `../.venv/bin/python schema.py`, which writes `schema/core_v0.schema.json`. After a schema change, run `../.venv/bin/python migrate_evidence.py` (add `--dry-run` to preview): it re-validates every stored evidence row and writes nothing if any row fails.

The pipeline also writes `data/papers/exclusions.jsonl` (each excluded paper with its reason) and `data/papers/unresolved.jsonl`.

## Extraction (`extract.py`)

Two independent Claude passes read each paper. The paper text is prompt-cached, so the second pass costs little input. Code then checks every quote against the full text, matches rows across passes, and validates each row against `EvidenceRow`:

- **ai_consistent:** both passes agree on the critical fields (value, unit, direction, uncertainty, dose, n, design, species).
- **ai_disputed:** the passes differ. Both values are kept under `extended.pass_differences`.
- **single_pass:** only one pass found the row. Rows that only pass b found are also marked `extended.unpaired_pass_b`. Rows pair when substance, dose, time, scale and probes match and the endpoint wording overlaps, so a reworded endpoint doesn't become two rows.
- **Rejected:** rows with no quote that matches the paper, and rows that fail the schema, go to `data/evidence/rejected_rows.jsonl`.
- **Screening:** each paper gets a yes/no on whether it reports measured outcomes, in `screening.jsonl`. Usage and cost for every call go to `extraction_runs.jsonl`.

Set `ANTHROPIC_API_KEY` in your shell or a gitignored `.env` (or run `ant auth login`), then:

```bash
cd pipeline
../.venv/bin/python extract.py --split dev        # 6 dev papers first; check the results
../.venv/bin/python extract.py --split heldout    # then the held-out papers
```

**Model and cost:** the default model is `claude-opus-5-5` at effort `high`, with server-side refusal fallback on. A rough estimate is $0.50–1.50 per paper for two passes, so about $20–50 for the 34 papers with full text. Each run prints its estimated cost. `--model claude-sonnet-5-5` costs about half, `--passes 1` skips the agreement check, and `--effort medium` reduces thinking.

**Hand-extracted corpus (no API):** the whole corpus so far was extracted by hand in Claude Code sessions, under `manual/`:

- `manual/helpers.py` — builders that produce `Extraction`-shaped drafts.
- `manual/build_dev_drafts.py` — the first 6 dev papers.
- `manual/batches/batch1_neuro.py` … `batch5_clinical.py` — the rest, grouped by topic.

Each batch writes a JSON file to `data/evidence/`, which `extract.py --from-drafts` loads through the same quote check and schema validation as the API path. These rows carry `pipeline_version: manual-claude-session-0.1` and `agreement: single_pass`. Running `extract.py` with an API key on the same papers replaces them.

**Frozen split:** `data/papers/frozen_split.json` fixes corpus membership and the dev/held-out split. Changes are listed under its `changes` key.
**Screening:** papers with no measured outcomes (hypothesis papers, qualitative studies, program descriptions) get `reports_measured_outcomes: false` and no rows.
