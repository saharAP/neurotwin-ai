# NeuroTwin AI

**How substances, lifestyle and environment change the brain, with every number traced to its source.**

NeuroTwin AI turns scattered neuroscience papers into comparable, source-linked measurements of how neurons change: **neurogenesis**, **neuroplasticity** (spinogenesis, dendritogenesis, synaptic change) and **neurodegeneration**. It covers any intervention: substances and medicines, exercise, sleep, meditation, environment and creative activity.

Direct cellular experiments in a living human brain are not possible, so this evidence comes from animal studies and cultured cells, including human stem-cell-derived neurons and organoids. It is spread over thousands of papers that use different endpoints, doses and time points. NeuroTwin AI organises it by outcome, shows each study against its own control, and keeps the exact sentence each number came from. Benefits, harms and null results are kept alike, and nothing is pooled into a single score.

- Project page: [`site/`](site/index.html)
- Pitch deck: [Google Drive (PDF)](https://drive.google.com/file/d/1_vWow-CKiTYg-4b31m6fYOt1xeQMsxxy/view?usp=sharing)
- Contact: Zeinab Alipanahloo, [sahar.aplo@gmail.com](mailto:sahar.aplo@gmail.com)

## Status

Early prototype (MVP v0, November 2026). **Research use only**: no medical, dosing or lifestyle advice.

- 65 papers found and legally retrieved through Europe PMC.
- 165 measurements extracted from 32 papers; 26 neuron-level values from 8 studies are in the atlas.
- Every extracted quote is checked in code against the paper text.
- Extraction accuracy is **not yet measured**, and no record has been reviewed by an expert. The outcome and endpoint lists are drafts awaiting review by a neuroscientist.

The first test corpus is three compounds plus exercise; which interventions are collected is set in [`config/interventions.json`](config/interventions.json). See [`docs/MVP_V0.md`](docs/MVP_V0.md) for the full status and plan.

## Repository

| Path | What it is |
|---|---|
| [`site/`](site) | Static project page, published with GitHub Pages |
| [`pipeline/`](pipeline) | Paper discovery, full-text retrieval, extraction and validation ([README](pipeline/README.md)) |
| [`schema/`](schema) | JSON schema for evidence records |
| [`config/`](config) | Interventions to collect and the draft endpoint registry |
| [`data/`](data) | Pipeline outputs: discovered papers, corpus and extracted evidence. Licensed full text stays local and is not committed |
| [`web/`](web) | Read-only Next.js atlas over the pipeline output (early prototype, [README](web/README.md)) |
| [`docs/`](docs) | MVP specification and data dictionary |

## Running the atlas locally

```bash
cd web
npm install
npm run dev   # http://localhost:3000
```
