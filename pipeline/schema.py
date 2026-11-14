"""NeuroTwin AI core schema v0: the single source of truth for MVP v0 records.

A lean, machine-checked subset of docs/DATA_STRATEGY.md. Two record types:

* Publication  - one per paper (DATA_STRATEGY §4, core fields only).
* EvidenceRow  - one flat row per measurement (DATA_STRATEGY §6-9 + §13,
                 denormalized for v0), with an optional clinical extension.

Only core fields are required, and only core fields need a missing_reason when
empty. Anything else goes in `extended` (free-form, not validated).
Export the JSON Schema with:  python schema.py  ->  schema/core_v0.schema.json
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, Optional

from pydantic import (BaseModel, BeforeValidator, ConfigDict, Field, ValidationError,
                      field_validator, model_validator)

SCHEMA_VERSION = "core-0.4.0"
PIPELINE_VERSION = "mvp0-pipeline-0.4.0"

# ---------------------------------------------------------------------------
# Controlled vocabularies (values from DATA_STRATEGY unless marked "v0 addition")
# ---------------------------------------------------------------------------

CurationStatus = Literal["raw", "machine_extracted", "needs_review", "verified",
                         "rejected", "superseded"]
MissingReason = Literal["not_reported", "not_applicable", "not_accessible", "ambiguous",
                        "extraction_failed", "pending_review"]
SourceRole = Literal["primary_measurement", "review_discovery", "method_reference"]
FullTextAccess = Literal["abstract", "open_full_text", "licensed_full_text",
                         "user_supplied", "unavailable"]
PeerReviewStatus = Literal["peer_reviewed", "preprint", "unknown"]
PublicationType = Literal[
    "primary_experimental", "systematic_review", "narrative_review", "dataset",
    # v0 additions (the dictionary's list has no clinical/observational types):
    "clinical_trial", "observational_study", "case_report", "qualitative_study",
    "editorial_or_comment", "other",
]

StudyDesign = Literal[
    "randomized_controlled_trial", "nonrandomized_trial", "open_label_trial",
    "observational", "case_report_or_series", "survey",
    "animal_in_vivo", "ex_vivo", "in_vitro", "organoid", "computational",
]
HUMAN_DESIGNS = {"randomized_controlled_trial", "nonrandomized_trial", "open_label_trial",
                 "observational", "case_report_or_series", "survey"}
IndependentUnit = Literal["participant", "animal", "donor", "culture_well", "cell",
                          "slice", "other"]
# core-0.4.0: an arm can be any intervention, not only a compound. Non-substance arms have no
# dose (dose_value null with reason "not_applicable"); the protocol goes in `regimen`.
InterventionType = Literal["substance", "exercise", "sleep", "meditation", "diet",
                           "environment", "other"]
ComparatorType = Literal["placebo", "active", "waitlist", "vehicle", "untreated",
                         "baseline_within_subject", "none", "other"]
ScaleLevel = Literal["molecular", "cellular", "neurogenesis", "synaptic_structural",
                     "synaptic_functional", "circuit", "behavioral", "clinical"]
EffectDirection = Literal["increase", "decrease", "no_change", "mixed", "not_reported"]
EffectSizeType = Literal["absolute_difference", "ratio", "percent_change",
                         "standardized_mean_difference", "odds_ratio", "risk_ratio",
                         "hazard_ratio", "correlation", "other"]
UncertaintyType = Literal["SD", "SEM", "CI95", "CI_other", "IQR", "range", "none_reported"]
ValueOrigin = Literal["author_reported", "digitized_from_plot", "statistically_derived"]
AnchorLocation = Literal["abstract", "text", "table", "figure", "supplement"]
AgreementStatus = Literal["pending", "ai_consistent", "ai_disputed", "single_pass"]

# Time units (core-0.3.0): one canonical spelling per unit, so "day" and "days" compare equal.
# Only the spelling is normalized; the value is never converted to another unit.
TIME_UNIT_ALIASES = {
    "s": "seconds", "sec": "seconds", "secs": "seconds", "second": "seconds",
    "min": "minutes", "mins": "minutes", "minute": "minutes",
    "h": "hours", "hr": "hours", "hrs": "hours", "hour": "hours",
    "d": "days", "day": "days", "night": "days", "nights": "days",
    "wk": "weeks", "wks": "weeks", "week": "weeks",
    "mo": "months", "month": "months",
    "y": "years", "yr": "years", "yrs": "years", "year": "years",
}


def _canonical_time_unit(v):
    if isinstance(v, str):
        key = v.strip().lower()
        return TIME_UNIT_ALIASES.get(key, key) or None
    return v


TimeUnit = Annotated[Literal["seconds", "minutes", "hours", "days", "weeks", "months", "years"],
                     BeforeValidator(_canonical_time_unit)]
ENDPOINT_KEY = r"^[a-z0-9]+(_[a-z0-9]+)*$"


def endpoint_key(label: str) -> str:
    """snake_case comparison key for an endpoint label, e.g. "GRID-HAMD score" -> "grid_hamd_score"."""
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ---------------------------------------------------------------------------
# Shared record metadata (DATA_STRATEGY §3)
# ---------------------------------------------------------------------------

class RecordMeta(Strict):
    schema_version: str = SCHEMA_VERSION
    pipeline_version: str = PIPELINE_VERSION
    created_at: str
    updated_at: str
    curation_status: CurationStatus = "raw"
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[str] = None


class CoreRecord(Strict):
    """Base: empty core fields must carry a missing_reason, filled ones must not."""
    meta: RecordMeta
    missing_reasons: dict[str, MissingReason] = Field(default_factory=dict)
    extended: dict[str, Any] = Field(default_factory=dict)

    # Core fields that may be None (subclasses list them).
    NULLABLE_CORE: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def _missingness(self):
        for name in self.NULLABLE_CORE:
            empty = _get(self, name) in (None, "", [])
            has_reason = name in self.missing_reasons
            if empty and not has_reason:
                raise ValueError(f"{name} is empty without a missing_reason")
            if not empty and has_reason:
                raise ValueError(f"{name} has a value and a missing_reason")
        unknown = set(self.missing_reasons) - set(self.NULLABLE_CORE)
        if unknown:
            raise ValueError(f"missing_reasons for non-core fields: {sorted(unknown)}")
        return self


def _get(obj: BaseModel, dotted: str):
    for part in dotted.split("."):
        obj = getattr(obj, part) if obj is not None else None
    return obj


# ---------------------------------------------------------------------------
# Publication (DATA_STRATEGY §4, core)
# ---------------------------------------------------------------------------

class Publication(CoreRecord):
    publication_id: str = Field(pattern=r"^pub_[0-9a-f]{16}$")
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = Field(default=None, pattern=r"^PMC\d+$")
    title: str = Field(min_length=1)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    journal: Optional[str] = None
    publication_type: PublicationType
    peer_review_status: PeerReviewStatus
    is_retracted: bool
    license: Optional[str] = None  # SPDX id or LicenseRef-*
    full_text_access: FullTextAccess
    source_role: SourceRole

    NULLABLE_CORE = ("doi", "year", "journal", "license")

    @model_validator(mode="after")
    def _identifier(self):
        if not (self.doi or self.pmid or self.pmcid):
            raise ValueError("publication needs at least one of doi, pmid, pmcid")
        return self


# ---------------------------------------------------------------------------
# EvidenceRow: one measurement, flat (DATA_STRATEGY §6-9, §13)
# ---------------------------------------------------------------------------

class SourceAnchor(Strict):
    location: AnchorLocation
    section: Optional[str] = None          # e.g. "Results"
    label: Optional[str] = None            # e.g. "Table 2", "Fig. 3b"
    quote: str = Field(min_length=3, max_length=400)  # verbatim; checked against full text
    quote_verified: bool = False           # set by code, never by the LLM


class Experiment(Strict):
    label: str                             # e.g. "Main trial", "Fig. 2 culture assay"
    design: StudyDesign
    species: str                           # lower-cased: "human", "mouse", "rat", ...
    population_or_model: str               # e.g. "adults with MDD", "rat cortical neurons"
    n: Optional[int] = Field(default=None, ge=1)
    independent_unit: IndependentUnit

    @field_validator("species")
    @classmethod
    def _lower_species(cls, v: str) -> str:
        return v.lower()


class Arm(Strict):
    label: str
    intervention_original: str             # exact author wording
    intervention_normalized: str           # e.g. "Psilocybin", "aerobic exercise"; "none" for control arms
    intervention_type: InterventionType = "substance"
    dose_value: Optional[float] = None
    dose_unit: Optional[str] = None        # original unit, never converted
    route: Optional[str] = None
    regimen: Optional[str] = None          # e.g. "2 doses, 1 week apart", "40 min treadmill, 3x/week, 12 weeks"
    comparator_label: Optional[str] = None
    comparator_type: ComparatorType


class Measurement(Strict):
    endpoint_original: str                 # exact label, e.g. "GRID-HAMD score"
    endpoint_normalized: str = Field(pattern=ENDPOINT_KEY)  # same outcome -> same key
    scale_level: ScaleLevel
    assay_or_instrument: Optional[str] = None
    time_value: Optional[float] = None
    time_unit: Optional[TimeUnit] = None
    time_origin: Optional[str] = None      # e.g. "first dose", "baseline"
    value: Optional[float] = None
    value_unit: Optional[str] = None
    control_value: Optional[float] = None
    effect_direction: EffectDirection
    effect_size_type: Optional[EffectSizeType] = None
    effect_size_value: Optional[float] = None
    uncertainty_type: UncertaintyType = "none_reported"
    uncertainty_low: Optional[float] = None    # SD/SEM value, or interval low
    uncertainty_high: Optional[float] = None   # interval high (CI/IQR/range)
    statistical_test: Optional[str] = None
    p_value: Optional[str] = Field(default=None, pattern=r"^(<|>|<=|=)?\s?\d*\.?\d+(e-?\d+)?$")
    value_origin: ValueOrigin = "author_reported"


class AdverseEvent(Strict):
    name: str
    arm_label: str
    n_participants_with_event: Optional[int] = Field(default=None, ge=0)
    n_participants_in_arm: Optional[int] = Field(default=None, ge=1)
    severity: Optional[Literal["mild", "moderate", "severe", "serious", "not_reported"]] = None


class ClinicalExtension(Strict):
    """Human-study fields missing from the culture-focused dictionary."""
    scale_name: Optional[str] = None               # e.g. "MADRS", "GRID-HAMD-17"
    higher_score_means: Optional[Literal["worse", "better"]] = None
    responder_rate: Optional[float] = Field(default=None, ge=0, le=1)
    remission_rate: Optional[float] = Field(default=None, ge=0, le=1)
    response_definition: Optional[str] = None
    blinding_integrity_assessed: Optional[Literal["yes", "no", "unclear"]] = None
    follow_up: Optional[str] = None
    adverse_events: list[AdverseEvent] = Field(default_factory=list)


class MechanismProbe(Strict):
    """A co-treatment used to test mechanism, e.g. ketanserin blocking 5-HT2A."""
    agent: str                                    # e.g. "ketanserin", "ANA-12", "TrkB knockout"
    target: Optional[str] = None                  # e.g. "5-HT2A receptor", "TrkB"
    probe_type: Literal["antagonist", "inhibitor", "agonist", "genetic_knockout",
                        "genetic_knockdown", "other"]
    dose_value: Optional[float] = None
    dose_unit: Optional[str] = None               # original unit, never converted
    effect_on_response: Optional[Literal["blocked", "reduced", "no_change", "enhanced",
                                         "not_reported"]] = None


class PreclinicalExtension(Strict):
    """Neuron-level variables for cell, tissue and animal studies (DATA_STRATEGY §6, §9)."""
    cell_type: Optional[str] = None               # author label, e.g. "cortical pyramidal neurons"
    brain_region: Optional[str] = None            # e.g. "prefrontal cortex", "dentate gyrus"
    culture_age_value: Optional[float] = None     # days in vitro or organoid age
    culture_age_unit: Optional[str] = None        # e.g. "DIV", "weeks"
    animal_age: Optional[str] = None              # as reported, e.g. "8-10 weeks", "P21"
    sex: Optional[Literal["male", "female", "both", "not_reported"]] = None
    strain_or_line: Optional[str] = None          # e.g. "C57BL/6J", "iPSC line WTC11"
    probes: list[MechanismProbe] = Field(default_factory=list)


class EvidenceRow(CoreRecord):
    evidence_id: str = Field(pattern=r"^meas_[0-9a-f]{16}$")
    publication_id: str = Field(pattern=r"^pub_[0-9a-f]{16}$")
    experiment: Experiment
    arm: Arm
    measurement: Measurement
    anchors: list[SourceAnchor] = Field(min_length=1)
    clinical: Optional[ClinicalExtension] = None
    preclinical: Optional[PreclinicalExtension] = None
    extraction_pass: Literal["a", "b", "merged"]
    agreement: AgreementStatus = "pending"

    NULLABLE_CORE = ("experiment.n", "arm.dose_value", "measurement.value",
                      "measurement.time_value")

    @model_validator(mode="after")
    def _scientific_rules(self):
        m, a, e = self.measurement, self.arm, self.experiment
        if a.dose_value is not None and not a.dose_unit:
            raise ValueError("dose_value needs its original dose_unit")
        if a.intervention_type != "substance" and a.dose_value is None and not a.regimen:
            raise ValueError("a non-substance arm needs its protocol in regimen (what, how long, how often)")
        if m.value is not None and not m.value_unit:
            raise ValueError("value needs value_unit")
        if m.time_value is not None and not (m.time_unit and m.time_origin):
            raise ValueError("time_value needs time_unit and time_origin")
        if m.uncertainty_type in {"CI95", "CI_other", "IQR", "range"} and (
                m.uncertainty_low is None or m.uncertainty_high is None):
            raise ValueError(f"{m.uncertainty_type} needs both bounds")
        is_human_study = e.design in HUMAN_DESIGNS
        if m.scale_level == "clinical" and not is_human_study:
            raise ValueError("clinical endpoints require a human study design; "
                             "cultures/animals are never clinical evidence")
        if is_human_study and e.species.lower() != "human":
            raise ValueError("human study design with non-human species")
        if self.preclinical is not None:
            pc = self.preclinical
            if is_human_study:
                raise ValueError("preclinical extension is for cell, tissue and animal studies")
            if pc.culture_age_value is not None and not pc.culture_age_unit:
                raise ValueError("culture_age_value needs culture_age_unit")
            for probe in pc.probes:
                if probe.dose_value is not None and not probe.dose_unit:
                    raise ValueError("probe dose_value needs its original dose_unit")
        if self.clinical is not None and not is_human_study:
            raise ValueError("clinical extension only applies to human studies")
        return self


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(prefix: str, key: str) -> str:
    """Namespaced, deterministic ID (§2): same source key -> same ID every run."""
    return f"{prefix}_{hashlib.sha256(key.lower().encode()).hexdigest()[:16]}"


def validate(model: type[BaseModel], record: dict) -> list[str]:
    try:
        model.model_validate(record)
        return []
    except ValidationError as exc:
        return [f"{'.'.join(map(str, e['loc'])) or '<record>'}: {e['msg']}" for e in exc.errors()]


def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def export_json_schema(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "core_v0.schema.json"
    bundle = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"NeuroTwin AI core schema {SCHEMA_VERSION}",
        "description": "Generated from pipeline/schema.py; do not edit by hand.",
        "$defs": {
            "Publication": Publication.model_json_schema(),
            "EvidenceRow": EvidenceRow.model_json_schema(),
        },
    }
    path.write_text(json.dumps(bundle, indent=2) + "\n")
    return [path]


if __name__ == "__main__":
    for p in export_json_schema(Path(__file__).resolve().parent.parent / "schema"):
        print(f"wrote {p}")
