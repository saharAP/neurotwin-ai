"""Step 5: extract measured outcomes from corpus full texts into EvidenceRow records.

Two independent LLM passes read each paper (the paper text is prompt-cached so
the second pass costs little input). Code then:
  1. checks every source quote really appears in the paper (rows whose quotes
     are all missing are rejected, per docs/MVP_V0.md §4),
  2. matches rows across passes; agreeing critical fields -> "ai_consistent",
     differences -> "ai_disputed", rows seen by one pass -> "single_pass",
  3. validates each row against schema.EvidenceRow.

Usage (needs ANTHROPIC_API_KEY or an `ant auth login` profile):
    ../.venv/bin/python extract.py --split dev            # the 5 dev papers
    ../.venv/bin/python extract.py --paper PMC7643046     # one paper
    ../.venv/bin/python extract.py --split all --passes 2
Rows from manually authored drafts (no API) can be loaded with --from-drafts.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from common import CORPUS_FILE, DATA, ROOT, read_jsonl, write_jsonl
from jats_text import jats_to_text, normalize, quote_in_text
from schema import (AnchorLocation, ComparatorType, EffectDirection, EffectSizeType,
                    EvidenceRow, IndependentUnit, MissingReason, PIPELINE_VERSION,
                    InterventionType, SCHEMA_VERSION, ScaleLevel, StudyDesign, TimeUnit, UncertaintyType,
                    ValueOrigin, endpoint_key, now_utc, stable_id, validate)

EVIDENCE_DIR = DATA / "evidence"
ROWS_FILE = EVIDENCE_DIR / "evidence_rows.jsonl"
REJECTED_FILE = EVIDENCE_DIR / "rejected_rows.jsonl"
SCREENING_FILE = EVIDENCE_DIR / "screening.jsonl"
RUNS_FILE = EVIDENCE_DIR / "extraction_runs.jsonl"

DEFAULT_MODEL = "claude-opus-5-5"
PRICES = {  # USD per million tokens: input, output, cache read, cache write (5 min)
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5),
}
TRACKED_MISSING = Literal["experiment.n", "arm.dose_value", "measurement.value",
                          "measurement.time_value"]


# ---------------------------------------------------------------------------
# LLM-facing draft models: same fields as schema.EvidenceRow parts, but without
# numeric bounds or regex patterns, so one malformed value can't sink the whole
# response. Every draft is converted and validated against EvidenceRow in code.
# ---------------------------------------------------------------------------

class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DraftExperiment(_M):
    label: str
    design: StudyDesign
    species: str
    population_or_model: str
    n: Optional[int]
    independent_unit: IndependentUnit


class DraftArm(_M):
    label: str
    intervention_original: str
    intervention_normalized: str
    intervention_type: InterventionType = "substance"
    dose_value: Optional[float]
    dose_unit: Optional[str]
    route: Optional[str]
    regimen: Optional[str]
    comparator_label: Optional[str]
    comparator_type: ComparatorType


class DraftMeasurement(_M):
    endpoint_original: str
    endpoint_normalized: Optional[str]
    scale_level: ScaleLevel
    assay_or_instrument: Optional[str]
    time_value: Optional[float]
    time_unit: Optional[TimeUnit]
    time_origin: Optional[str]
    value: Optional[float]
    value_unit: Optional[str]
    control_value: Optional[float]
    effect_direction: EffectDirection
    effect_size_type: Optional[EffectSizeType]
    effect_size_value: Optional[float]
    uncertainty_type: UncertaintyType
    uncertainty_low: Optional[float]
    uncertainty_high: Optional[float]
    statistical_test: Optional[str]
    p_value: Optional[str]
    value_origin: ValueOrigin


class DraftAnchor(_M):
    location: AnchorLocation
    section: Optional[str]
    label: Optional[str]
    quote: str


class DraftAdverseEvent(_M):
    name: str
    arm_label: str
    n_participants_with_event: Optional[int]
    n_participants_in_arm: Optional[int]
    severity: Optional[Literal["mild", "moderate", "severe", "serious", "not_reported"]]


class DraftClinical(_M):
    scale_name: Optional[str]
    higher_score_means: Optional[Literal["worse", "better"]]
    responder_rate: Optional[float]
    remission_rate: Optional[float]
    response_definition: Optional[str]
    blinding_integrity_assessed: Optional[Literal["yes", "no", "unclear"]]
    follow_up: Optional[str]
    adverse_events: list[DraftAdverseEvent]


class DraftProbe(_M):
    agent: str
    target: Optional[str]
    probe_type: Literal["antagonist", "inhibitor", "agonist", "genetic_knockout",
                        "genetic_knockdown", "other"]
    dose_value: Optional[float]
    dose_unit: Optional[str]
    effect_on_response: Optional[Literal["blocked", "reduced", "no_change", "enhanced",
                                         "not_reported"]]


class DraftPreclinical(_M):
    cell_type: Optional[str]
    brain_region: Optional[str]
    culture_age_value: Optional[float]
    culture_age_unit: Optional[str]
    animal_age: Optional[str]
    sex: Optional[Literal["male", "female", "both", "not_reported"]]
    strain_or_line: Optional[str]
    probes: list[DraftProbe]


class DraftMissing(_M):
    field: TRACKED_MISSING
    reason: MissingReason


class DraftRow(_M):
    experiment: DraftExperiment
    arm: DraftArm
    measurement: DraftMeasurement
    anchors: list[DraftAnchor] = Field(description="1-2 verbatim quotes from the paper text")
    clinical: Optional[DraftClinical]
    preclinical: Optional[DraftPreclinical]
    missing: list[DraftMissing]


class Extraction(_M):
    reports_measured_outcomes: bool
    screening_reason: str = Field(description="One sentence: why the paper does or does not report measured outcomes")
    measurements: list[DraftRow]


SYSTEM_PROMPT = """You extract measured outcomes from one scientific paper into structured records for a research evidence database used by neuroscientists. Accuracy and traceability matter more than coverage.

Rules:
- Extract only results this paper itself reports (Results text, tables, figure captions, abstract). Never extract values the paper cites from other studies.
- One record = one arm (or group) x one endpoint x one time point. Include null / no-change results and adverse events, not just positive findings.
- Keep every number and unit exactly as reported. Never convert doses or units, never compute values the paper does not state. If a value is only shown in a plot, leave `value` null with reason "not_reported" rather than estimating.
- When a tracked field is unknown (experiment.n, arm.dose_value, measurement.value, measurement.time_value), set it to null and add it to `missing` with a reason. Do not list fields that have values.
- `anchors[].quote` must be copied character-for-character from the paper text you were given (20-300 characters) and should contain the reported value or finding. Quotes are checked automatically; a record with no matching quote is discarded.
- `endpoint_original` names the outcome only (e.g. "QIDS-SR16 depression score", "dendritic spine density"), never the time point or arm; put time in `time_value`/`time_unit`. Give the same outcome the same `endpoint_normalized` snake_case key across arms and time points.
- `effect_direction` is the direction of change versus the comparator (or baseline), not whether it is good or bad.
- `design`: pick the closest study design. Use human designs only for studies in people. Cultured human cells (e.g. iPSC neurons) are "in_vitro" with species "human"; organoids are "organoid".
- `clinical`: only for human studies (rating scale, response/remission, adverse events, blinding check, follow-up). `preclinical`: only for cell, tissue and animal studies (cell type, brain region, culture or animal age, sex, strain/line, and mechanism probes such as receptor antagonists or knockouts with their target and whether they blocked the response).
- `intervention_normalized`: the name of what the arm received, as a substance (e.g. "Psilocybin", "Creatine", "Ketamine") or a non-substance intervention (e.g. "aerobic exercise", "sleep deprivation", "environmental enrichment"), or "none" for control arms. Set `intervention_type` to match.
- For a non-substance arm there is no dose: leave `dose_value` null with reason "not_applicable" and describe the protocol in `regimen` (what was done, intensity, duration, frequency). Record what the paper says was achieved if it differs from what was assigned.
- If the paper reports no measured outcomes (hypothesis, review, commentary, protocol, purely qualitative interviews), set `reports_measured_outcomes` to false and return no measurements.
- Return at most 40 records. Prioritize primary endpoints, mechanism-probe results, and dose or time series."""

PASS_INSTRUCTIONS = {
    "a": "Extract the measured outcomes from the paper above.",
    "b": ("Independently extract the measured outcomes from the paper above. Work from the "
          "tables and results text first, and be conservative: leave a value null rather than guess."),
}


# ---------------------------------------------------------------------------
# Draft -> EvidenceRow
# ---------------------------------------------------------------------------

def row_key(d: dict) -> str:
    m, a = d["measurement"], d["arm"]
    t = "" if m["time_value"] is None else f"{m['time_value']:g}{normalize(m['time_unit'] or '')}"
    return "|".join([normalize(m["endpoint_original"]), normalize(a["label"]), t])


def to_evidence_row(pub_id: str, draft: dict, text_norm: str, *, pass_label: str,
                    pipeline_version: str) -> tuple[dict | None, str | None]:
    anchors = []
    for a in draft["anchors"]:
        anchors.append({**a, "quote": a["quote"][:400],
                        "quote_verified": quote_in_text(a["quote"], text_norm)})
    anchors = [a for a in anchors if len(a["quote"]) >= 3]
    if not any(a["quote_verified"] for a in anchors):
        return None, "no source quote found in the paper text"
    ts = now_utc()
    row = {
        "meta": {"schema_version": SCHEMA_VERSION, "pipeline_version": pipeline_version,
                 "created_at": ts, "updated_at": ts, "curation_status": "machine_extracted",
                 "reviewer_id": None, "reviewed_at": None},
        "evidence_id": "",
        "publication_id": pub_id,
        "experiment": draft["experiment"],
        "arm": draft["arm"],
        "measurement": draft["measurement"],
        "anchors": anchors,
        "clinical": draft.get("clinical"),
        "preclinical": draft.get("preclinical"),
        "extraction_pass": pass_label,
        "agreement": "single_pass",
        "missing_reasons": {m["field"]: m["reason"] for m in draft.get("missing", [])},
        "extended": {},
    }
    # Every row needs a comparison key; derive it from the author's label when the pass gave none.
    m = row["measurement"]
    if not m.get("endpoint_normalized"):
        m["endpoint_normalized"] = endpoint_key(m["endpoint_original"])
    # Keep missing_reasons consistent with the values actually present.
    for field in list(row["missing_reasons"]):
        section, name = field.split(".")
        if row[section].get(name) is not None:
            del row["missing_reasons"][field]
    for field in ("experiment.n", "arm.dose_value", "measurement.value", "measurement.time_value"):
        section, name = field.split(".")
        if row[section].get(name) is None and field not in row["missing_reasons"]:
            row["missing_reasons"][field] = "not_reported"
    return row, None


CRITICAL = [("measurement", "value"), ("measurement", "value_unit"), ("measurement", "effect_direction"),
            ("measurement", "uncertainty_low"), ("measurement", "uncertainty_high"),
            ("arm", "dose_value"), ("arm", "dose_unit"), ("experiment", "n"),
            ("experiment", "design"), ("experiment", "species")]


def _same(x, y) -> bool:
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        return abs(float(x) - float(y)) <= 1e-9 * max(1.0, abs(float(x)))
    if isinstance(x, str) and isinstance(y, str):
        return normalize(x) == normalize(y)
    return x == y


def _condition(d: dict) -> tuple:
    """What was measured under which condition, independent of how a pass worded it."""
    a, m = d["arm"], d["measurement"]
    probes = tuple(sorted(normalize(p["agent"]) for p in (d.get("preclinical") or {}).get("probes", [])))
    return (normalize(a["intervention_normalized"]), a["dose_value"], normalize(a["dose_unit"] or ""),
            m["time_value"], normalize(m["time_unit"] or ""), m["scale_level"], probes)


def _words(d: dict) -> set[str]:
    m = d["measurement"]
    text = f"{m['endpoint_original']} {m['endpoint_normalized'] or ''} {m['assay_or_instrument'] or ''}"
    return {w for w in re.split(r"[^a-z0-9]+", normalize(text)) if len(w) > 1}


def _similarity(x: dict, y: dict) -> float:
    a, b = _words(x), _words(y)
    return len(a & b) / max(1, len(a | b))


def merge_passes(rows_a: list[dict], rows_b: list[dict]) -> list[dict]:
    """Pair each pass-a row with the pass-b row for the same measurement.

    Rows pair when the condition (substance, dose, time, scale, probes) is identical and the
    endpoint wording overlaps (Jaccard >= 0.5 on words; exact endpoint key wins first).
    Unpaired pass-b rows are kept but marked `extended.unpaired_pass_b`, so the UI and
    stats can tell them apart from rows both passes found.
    """
    unused = list(range(len(rows_b)))
    merged = []
    for r in rows_a:
        cands = [i for i in unused if _condition(rows_b[i]) == _condition(r)]
        exact = [i for i in cands if row_key(rows_b[i]) == row_key(r)]
        best = exact[0] if exact else max(cands, key=lambda i: _similarity(r, rows_b[i]), default=None)
        if best is None or (not exact and _similarity(r, rows_b[best]) < 0.5):
            merged.append(r)  # single_pass, found by pass a only
            continue
        unused.remove(best)
        other = rows_b[best]
        diffs = {f"{s}.{f}": {"a": r[s].get(f), "b": other[s].get(f)}
                 for s, f in CRITICAL if not _same(r[s].get(f), other[s].get(f))}
        r = {**r, "extraction_pass": "merged",
             "agreement": "ai_disputed" if diffs else "ai_consistent"}
        if diffs:
            r["extended"] = {**r["extended"], "pass_differences": diffs}
        merged.append(r)
    for i in unused:
        merged.append({**rows_b[i], "extended": {**rows_b[i]["extended"], "unpaired_pass_b": True}})
    return merged


def finalize(pub_id: str, rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Assign stable IDs and validate; returns (valid rows, rejected rows)."""
    seen: dict[str, int] = {}
    valid, rejected = [], []
    for r in rows:
        k = row_key(r)
        seen[k] = seen.get(k, 0) + 1
        r["evidence_id"] = stable_id("meas", f"{pub_id}|{k}|{seen[k]}")
        if errs := validate(EvidenceRow, r):
            rejected.append({"publication_id": pub_id, "reason": "schema", "errors": errs, "row": r})
        else:
            valid.append(EvidenceRow.model_validate(r).model_dump(mode="json"))
    return valid, rejected


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def call_pass(client, model: str, effort: str, paper_text: str, pass_label: str):
    # Streamed: a 32k-token structured response can exceed the SDK's non-streaming limit.
    with client.beta.messages.stream(
        model=model,
        max_tokens=32000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": effort},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "<paper>\n" + paper_text + "\n</paper>",
             "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": PASS_INSTRUCTIONS[pass_label]},
        ]}],
        output_format=Extraction,
    ) as stream:
        return stream.get_final_message()


def usage_cost(model: str, usage) -> float:
    p_in, p_out, p_read, p_write = PRICES.get(model, PRICES[DEFAULT_MODEL])
    return ((usage.input_tokens or 0) * p_in + (usage.output_tokens or 0) * p_out
            + (getattr(usage, "cache_read_input_tokens", 0) or 0) * p_read
            + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * p_write) / 1e6


# ---------------------------------------------------------------------------
# Output files: rows for re-extracted papers are replaced, others kept.
# ---------------------------------------------------------------------------

def save(pub_ids: set[str], rows: list[dict], rejected: list[dict], screening: list[dict]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    def replace(path: Path, new: list[dict]) -> None:
        old = [r for r in read_jsonl(path)] if path.exists() else []
        write_jsonl(path, [r for r in old if r.get("publication_id") not in pub_ids] + new)

    replace(ROWS_FILE, rows)
    replace(REJECTED_FILE, rejected)
    replace(SCREENING_FILE, screening)


def log_run(entry: dict) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with RUNS_FILE.open("a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def load_text(pub: dict) -> tuple[str, str]:
    path = ROOT / pub["extended"]["fulltext"]["file"]
    text = jats_to_text(path)
    return text, normalize(text)


def run_api(pubs: list[dict], model: str, effort: str, passes: int) -> None:
    import anthropic
    client = anthropic.Anthropic()
    total = 0.0
    for pub in pubs:
        pid, pmcid = pub["publication_id"], pub["pmcid"]
        text, text_norm = load_text(pub)
        per_pass, screening, rejected = {}, None, []
        for label in ["a", "b"][:passes]:
            try:
                resp = call_pass(client, model, effort, text, label)
            except anthropic.APIStatusError as e:
                print(f"  {pmcid} pass {label}: API error {e.status_code}: {e.message}")
                log_run({"publication_id": pid, "pass": label, "error": str(e), "at": now_utc()})
                break
            except Exception as e:  # e.g. output failed to parse
                print(f"  {pmcid} pass {label}: failed: {e}")
                log_run({"publication_id": pid, "pass": label, "error": repr(e), "at": now_utc()})
                break
            cost = usage_cost(model, resp.usage)
            total += cost
            log_run({"publication_id": pid, "pmcid": pmcid, "pass": label, "model": resp.model,
                     "effort": effort, "stop_reason": resp.stop_reason,
                     "input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens,
                     "cache_read": getattr(resp.usage, "cache_read_input_tokens", None),
                     "cache_write": getattr(resp.usage, "cache_creation_input_tokens", None),
                     "cost_usd": round(cost, 4), "at": now_utc()})
            if resp.stop_reason in ("refusal", "max_tokens") or resp.parsed_output is None:
                print(f"  {pmcid} pass {label}: stopped ({resp.stop_reason}), skipped")
                break
            out: Extraction = resp.parsed_output
            screening = screening or {"publication_id": pid, "pmcid": pmcid,
                                      "reports_measured_outcomes": out.reports_measured_outcomes,
                                      "reason": out.screening_reason, "model": resp.model,
                                      "at": now_utc()}
            rows = []
            for d in out.measurements:
                row, why = to_evidence_row(pid, d.model_dump(), text_norm, pass_label=label,
                                           pipeline_version=PIPELINE_VERSION)
                if row:
                    rows.append(row)
                else:
                    rejected.append({"publication_id": pid, "reason": why, "pass": label,
                                     "draft": d.model_dump()})
            per_pass[label] = rows
        if not per_pass:
            continue
        merged = (merge_passes(per_pass["a"], per_pass["b"]) if len(per_pass) == 2
                  else next(iter(per_pass.values())))
        valid, bad = finalize(pid, merged)
        save({pid}, valid, rejected + bad, [screening] if screening else [])
        agree = {k: sum(r["agreement"] == k for r in valid) for k in ("ai_consistent", "ai_disputed", "single_pass")}
        print(f"  {pmcid}: {len(valid)} rows {agree}, rejected {len(rejected) + len(bad)}")
    print(f"estimated API cost: ${total:.2f}")


def run_drafts(path: Path, pubs_by_pmcid: dict[str, dict], pipeline_version: str) -> None:
    """Load hand-authored drafts: {"PMCxxxx": {"reports_measured_outcomes": .., "screening_reason": .., "measurements": [...]}}."""
    drafts = json.loads(path.read_text())
    for pmcid, payload in drafts.items():
        pub = pubs_by_pmcid[pmcid]
        pid = pub["publication_id"]
        ext = Extraction.model_validate(payload)
        _, text_norm = load_text(pub)
        rows, rejected = [], []
        for d in ext.measurements:
            row, why = to_evidence_row(pid, d.model_dump(), text_norm, pass_label="a",
                                       pipeline_version=pipeline_version)
            if row:
                rows.append(row)
            else:
                rejected.append({"publication_id": pid, "reason": why, "draft": d.model_dump()})
        valid, bad = finalize(pid, rows)
        screening = {"publication_id": pid, "pmcid": pmcid,
                     "reports_measured_outcomes": ext.reports_measured_outcomes,
                     "reason": ext.screening_reason, "model": pipeline_version, "at": now_utc()}
        save({pid}, valid, rejected + bad, [screening])
        print(f"  {pmcid}: {len(valid)} rows, rejected {len(rejected) + len(bad)}"
              + "".join(f"\n    - {r['reason']}: {r.get('errors') or r.get('draft', {}).get('anchors')}"
                        for r in rejected + bad))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=["dev", "heldout", "all"], default="dev")
    ap.add_argument("--paper", action="append", help="PMCID; repeatable")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--passes", type=int, choices=[1, 2], default=2)
    ap.add_argument("--from-drafts", type=Path, help="load hand-authored drafts JSON instead of calling the API")
    ap.add_argument("--drafts-version", default="manual-claude-session-0.1")
    args = ap.parse_args()

    corpus = [p for p in read_jsonl(CORPUS_FILE)
              if p["extended"].get("fulltext", {}).get("fetch_status", "").startswith("ok")]
    if args.from_drafts:
        run_drafts(args.from_drafts, {p["pmcid"]: p for p in corpus}, args.drafts_version)
        return
    if args.paper:
        pubs = [p for p in corpus if p["pmcid"] in set(args.paper)]
    else:
        pubs = [p for p in corpus if args.split == "all" or p["extended"]["corpus"]["split"] == args.split]
    if not pubs:
        sys.exit("no matching papers with full text")
    print(f"extracting {len(pubs)} papers with {args.model} (effort {args.effort}, {args.passes} passes)")
    run_api(pubs, args.model, args.effort, args.passes)


if __name__ == "__main__":
    main()
