# NeuroTwin AI — MVP v0: Neuron Outcome Atlas

**Version:** 0.4 — 11 November 2026
**Status:** Redesign. The first build (paper pipeline, core schema core-0.4.0, read-only web app, 165 hand-extracted measurements) is done and is described in §2. Everything in §3–§9 marked **planned** is not built yet.
**Related:** [data dictionary](./DATA_STRATEGY.md).

## 0. Project subject

NeuroTwin AI is a neuroscience project. Its subject is **how neurons change under different substances and different environmental settings**: medicines, supplements and other compounds, and conditions such as exercise, sleep, meditation and surroundings. It records benefits, harms and null results alike, as set out in the business proposal.

**Outcome focus.** The outcomes are changes in neurons themselves: **neurogenesis** (new neurons), **spinogenesis** (new dendritic spines), **dendritogenesis** (dendrite growth and branching), **neuroplasticity** more broadly, and **neurodegenerative features** (loss of neurons, synapses or dendrites). These are kept as separate outcomes and never merged into one score.

The project is **not** about one class of compound. Psilocybin, DMT and 5-MeO-DMT were only the first test corpus. Which interventions are collected is one file, [config/interventions.json](../config/interventions.json); no code names a compound.

## 1. Purpose

v0 is a fast, low-cost build with AI and a small, fixed set of papers. It is meant to answer three questions:

1. **Data feasibility:** can primary papers on neuron-level outcomes be found, obtained legally, and turned into numbers that can be compared across studies?
2. **Extraction reliability:** can an AI pipeline extract those numbers with a measured error rate, with every value tied to the text that supports it?
3. **A demonstrable product:** a working, source-linked atlas that neuroscientists can react to. Their reaction is the first demand signal.

v0 does not test willingness to pay or repeat usage.

## 2. What the first build showed

The first build chose papers by substance and therapeutic area and extracted whatever each paper measured. Measured on 11 November 2026:

| Measure | Value |
|---|---|
| Corpus | 65 papers: 50 on the three compounds (47 read) and 15 on exercise (not read) |
| Measurements | 165, from 32 papers; 15 papers had no measured outcomes in scope |
| Neuron-level rows (neurogenesis, synaptic structure, cell survival and morphology) | 27 (16%), from 8 papers |
| Behavioral or clinical rows | 86 (52%) |
| Rows with a numeric value / a control value / an uncertainty | 72 / 36 / 29 |
| Distinct endpoint keys | 115; only 8 are shared by two or more papers |
| Source quotes from text / tables / figures or supplements | 163 / 3 / 0 |
| Rows checked by a second pass or a reviewer | 0 |

**What worked:** discovery and resolution through Europe PMC; legal full-text retrieval; a schema that rejects invalid records; a code check that every quote appears in its paper (it caught two mis-transcribed quotes); selection that ignores result direction and logs every exclusion; adding an intervention by configuration alone.

**What did not:**

- **The corpus does not match the subject.** Selecting by substance and therapeutic area pulled in clinical trials, not neuron studies.
- **Almost nothing is comparable.** Endpoint names are free text, and most rows have no control value.
- **The numbers are in figures and supplements**, which the pipeline does not read.
- **Accuracy is unmeasured.** All 165 rows were extracted by hand in one pass in Claude Code sessions. The API extraction path (`pipeline/extract.py`) has not been run, and the audit has not been done.

The redesign below keeps the working parts and changes what is collected and how it is shown.

## 3. Scope (planned)

The MVP is organised **by outcome, not by substance**.

- **Five canonical outcomes:** adult neurogenesis, dendritic spine density, dendritic complexity, synaptic markers, and neuron survival or loss (see §4).
- **Any intervention is the comparison axis:** the same outcome is shown under each intervention that has evidence for it.
- **Evidence:** preclinical only: cell cultures, animal studies, and human-derived cells and organoids. These outcomes cannot be measured directly in living people. Human imaging and clinical results become optional context, always labelled as proxies.
- **Reference interventions:** besides the three compounds, include interventions with deep neuron-level literatures so that comparison is possible: exercise, environmental enrichment, an SSRI (fluoxetine), and chronic stress as a negative reference. Each is an entry in `config/interventions.json`.
- **Corpus size:** 60–80 primary papers.
- **Out of scope for the atlas:** behavioral and clinical endpoints, therapeutic-area grouping, user uploads, prediction of any kind.

## 4. Canonical outcomes and endpoint registry (planned)

Every extracted measurement must map to one endpoint in a fixed registry (`config/endpoints.json`), or it is stored as unmapped and not shown in the atlas. This replaces free-text endpoint keys.

The list below is a **draft**. It must be reviewed by a neuroscientist before extraction starts.

| Outcome | Draft endpoints |
|---|---|
| Adult neurogenesis | BrdU+ or EdU+ cells, Ki-67+ cells, DCX+ cells, surviving new neurons (BrdU+/NeuN+) |
| Dendritic spine density | Spines per unit dendrite length, spine formation rate, spine elimination rate |
| Dendritic complexity | Sholl intersections, branch number, total dendritic length, neurite length |
| Synaptic markers | PSD-95, synaptophysin, SV2A, synapse counts |
| Neuron survival or loss | Neuron counts (e.g. NeuN+, TH+), apoptosis markers (cleaved caspase-3, TUNEL), cell viability |

BDNF and TrkB signalling are recorded as context markers, not as one of the five outcomes.

Rules for the registry: each endpoint has an id, a label, its outcome, its assay family and its unit family. Two measurements are comparable only within the same endpoint. Formation, elimination and net density stay separate endpoints.

## 5. Corpus and discovery (planned)

- **Search by outcome × intervention.** The Europe PMC search (`pipeline/search_literature.py`) already builds its query from the configuration. It will require an outcome term in the title, not only in the abstract.
- **Screen before the cap.** An abstract-level screen keeps papers that report a registry endpoint with numbers. The cap is applied after screening, in the same effect-blind order as now. The first build applied the cap first, which let a corrigendum and a trial-highlights note into the exercise set.
- **OPEN Foundation** stays one discovery path for the compounds it covers. It is used only to find papers; nothing from OPEN appears in the data or the product.
- **Frozen split.** `data/papers/frozen_split.json` continues to fix corpus membership and the dev/held-out split. Papers that leave the corpus under the new scope are recorded under its `changes` key.
- **Selection stays effect-blind:** no criterion looks at the direction or size of a result, and every exclusion is logged with its reason.

## 6. Data model changes (planned, core-0.5.0)

The current schema is [pipeline/schema.py](../pipeline/schema.py) (core-0.4.0). Planned changes:

| Change | Why |
|---|---|
| `endpoint_id` from the registry replaces the free-text endpoint key | One outcome, one key |
| `model_state`: healthy, or under an insult (stress, hypoxia, toxin, disease model, ageing), with the insult named | "Doubled new neurons" in stressed animals is a rescue, not the same finding as in healthy animals |
| Each row is a **contrast**: both groups' values, n and uncertainty | Most current rows have no control value |
| Percent change against the study's own control is computed in code and labelled as derived | A common scale for display without pooling |
| The extracted number must appear in its source quote, checked in code | The quote check proves the quote exists, not that the value matches it |
| Figure-only values are recorded as gaps with the figure reference | Today they are silently missing |
| Structured exposure for non-substance arms: modality, intensity, session length, frequency, total duration | Free-text `regimen` cannot be compared |

Carried over unchanged: original values and units, missing-value reasons, the preclinical extension (cell type, region, age, sex, strain, mechanism probes), and the rule that cell and animal results are never recorded as clinical evidence.

## 7. Pipeline (built, with planned changes)

**Built:** discover → resolve → select → fetch full text → extract → quote check → schema validation. See [pipeline/README.md](../pipeline/README.md).

**Planned changes:**

1. **Each step writes its own file.** Today selection rewrites `corpus.jsonl` and drops what the fetch step added to it.
2. **Read supplement tables.** Supplement archives are already downloaded for most papers.
3. **Two independent extraction passes** through `extract.py`. Fields where the passes agree are marked AI-consistent; differences are marked AI-disputed and both values are kept.
4. **Audit.** A person checks 100 randomly chosen fields against the papers. This measures the error rate; it is not curation.

Every record is labelled "AI-extracted — not expert-reviewed" and shows its agreement status.

## 8. Product: three screens (planned)

Users browse, compare and export. They do not upload papers.

| Screen | Content |
|---|---|
| **Atlas** | Outcome × intervention grid. Each cell shows the number of studies, the reported directions, the evidence levels, and gaps. |
| **Outcome page** | One row per study contrast: percent change against the study's own control, with its uncertainty where it can be computed. Filters for species, region, model state, dose and time. Every point opens its source quote. No pooled estimate and no fitted curve. |
| **Study page** | The paper, its contrasts, their quotes, and CSV/JSON export with citations and limitations. |

An About page reports how the corpus was built and the measured quality: audit error rate, two-pass agreement, and how many rows are reviewed.

**As built today:** eight pages (experiment explorer, explore, evidence gaps, map, papers, measurements, compare, about). The atlas replaces the map, gaps and explore pages; the outcome page replaces the experiment explorer, compare and measurements pages. The neuron drawing from the experiment explorer is kept on the outcome page, scaled by the measured ratio of the selected study.

## 9. Rules carried over unchanged

- Original values and units are kept. No cross-species dose conversion.
- Null, adverse and mixed results are shown. A missing safety report is not shown as "safe".
- The five outcomes are never merged. There is no composite score.
- Cultures, organoids and animal studies are never labelled as human brain evidence.
- Direction of change is not benefit or harm.
- Research use only: no dosing or treatment guidance.

## 10. Tech

Python pipeline (Europe PMC API, quote verification, Pydantic schema) and a Next.js app. The pipeline writes versioned JSONL files under `data/`, and the web app in `web/` reads them directly. There is no database, API server or login. Full texts stay local in `data/fulltext/` and are not committed. After a schema change, `pipeline/migrate_evidence.py` re-validates and rewrites the stored rows.

## 11. Validation gates (set before the rebuild)

| Question | Metric | Target |
|---|---|---|
| Comparability | Outcomes with at least 8 independent studies | ≥ 3 of 5 |
| Numeric completeness | Atlas rows with both group values and n | ≥ 70% |
| Anchoring | Rows whose value appears in a verified source quote | 100% (others rejected) |
| Agreement | Critical fields where both AI passes agree | ≥ 85% |
| Accuracy | Exactness in a human audit of 100 fields | ≥ 95% |
| Usefulness | Neuroscientists who complete a real question with the atlas | 3–5 people; time and trust recorded |

**Outcomes:**
- **Pass:** show the atlas to researchers; pick the first endpoint for deeper work from the outcome with the most comparable data.
- **Fail on comparability or completeness:** narrow to the one or two outcomes that have data, or add supplement and figure reading.
- **Fail on accuracy:** add human review before showing anyone.

## 12. What happens to the existing data

The 165 rows stay in `data/evidence/evidence_rows.jsonl`. After the registry exists:

- The 27 neuron-level rows are mapped to registry endpoints and move into the atlas.
- The other 138 rows (behavioral, clinical, circuit, molecular) are kept as context and are not shown in the atlas.
- One paper with full text (PMC12635168) is still not extracted, and the 15 exercise papers have not been read.

## 13. Steps

| # | Step | Status |
|---|---|---|
| 1 | Commit the first build | Done, 11 November 2026 |
| 2 | Audit the existing 165 rows (100 fields, by a person) | Not started |
| 3 | Draft the endpoint registry and have a neuroscientist review it | Draft in §4 |
| 4 | Schema core-0.5.0 (§6) and migration of the 27 neuron-level rows | Not started |
| 5 | Rebuild the corpus by outcome × intervention, screening before the cap | Not started |
| 6 | Extract with two passes; read supplement tables | Not started |
| 7 | Build the three screens | Not started |
| 8 | Run the validation gates | Not started |

## 14. Blockers and risks

- **No measured accuracy yet.** Steps 2 and 6 address this. Until then, nothing should be presented as validated.
- **No neuroscientist or user has reviewed the work.** The registry and the comparability rules need a domain expert (step 3), and the proposal's Phase 0 interviews have not happened.
- **Numbers in figures.** If supplement tables do not supply enough values, the numeric-completeness gate will fail and figure reading becomes necessary.
- **Licensing.** 14 of the 65 current papers carry non-commercial licences, and OPEN Foundation's terms are non-commercial. Resolve both before any public or commercial release.
- **Selection bias.** The corpus is what one search and OPEN's coverage reach, not a systematic review. The atlas must say so.
- **Reading the drawings as simulation.** The neuron drawing illustrates one measured ratio. It must stay labelled as a schematic.
