# NeuroTwin AI — Data Strategy and Parameter Dictionary

**Version:** 1.0 — November 2026  
**Companion:** the NeuroTwin AI business proposal (kept private)  
**Status:** Proposed research data contract; requires scientific and legal review before production.

> **MVP v0 core schema:** the machine-checked subset used by the pipeline lives in [pipeline/schema.py](../pipeline/schema.py) (exported to [schema/core_v0.schema.json](../schema/core_v0.schema.json)). It keeps about 25 required fields across `Publication` and a flat per-measurement `EvidenceRow`, adds a clinical extension (rating scale, response/remission, adverse events, blinding), and stores every other field in this dictionary as optional `extended` data. Where the two disagree for v0 records, the code is authoritative; this document remains the full target model. Current version: **core-0.4.0** (see §14, "v0 core normalization").

## 1. Purpose and guiding rules

This document defines the entities, parameters, relationships, units, evidence levels, provenance, quality controls, and training-readiness gates for NeuroTwin AI. The immediate goal is to support trustworthy **paper → research question → experiment → outcome → mechanism** analysis; future modeling is conditional on independently validated data.

**Non-negotiable design rules:**
1. Preserve **author-stated** research questions separately from **AI-inferred** questions.
2. Store every distinct experimental arm, measurement, endpoint, and time point separately.
3. Never equate neurogenesis, dendritogenesis, synaptogenesis, circuit function, and clinical improvement.
4. Distinguish the original numeric measurement from conversions, normalization, derived estimates, and hypotheses.
5. Every supported result and graph edge must link back to a paper location or permitted source-data record.
6. Record source species, model, cell type, brain region, chemical identity, route, units, and time.
7. Use `null` plus a missingness reason rather than guessing absent measurements.
8. Separate **observed**, **statistically modeled**, **mechanistic simulated**, and **illustrative** content.
9. Mark applicability limits and abstain from unsupported predictions.
10. Reviews are discovery sources; primary experiments and their data are evidence for measured outcomes.

## 2. Entity relationships and cardinality

```text
Publication (1)
  ├── (0..N) ResearchQuestion
  │     └── (0..N) Hypothesis
  ├── (0..N) Experiment
  │     ├── (1..N) ExperimentalArm
  │     │     └── (0..N) InterventionExposure
  │     ├── (0..N) SampleGroup
  │     └── (0..N) Measurement
  │           ├── (1) EndpointDefinition
  │           ├── (0..N) StatisticalResult
  │           └── (1..N) SourceAnchor
  └── (0..N) Claim

MechanismNode ⇄ MechanismEvidenceEdge ⇄ MechanismNode
                              └── source experiment/measurement/claim

Experiment ⇄ CrossModelComparison ⇄ Experiment
Publication/Experiment/Measurement/Edge ⇄ EvidenceAssessment
```

Identifiers must be stable and namespaced: `pub_`, `rq_`, `hyp_`, `exp_`, `arm_`, `int_`, `sample_`, `meas_`, `stat_`, `endpoint_`, `node_`, `edge_`, `anchor_`, `claim_`, `assessment_`.

### Entity constraints

- A publication can ask multiple research questions and contain multiple experiments.
- An experiment can test several hypotheses and measure multiple outcomes.
- A single arm can have multiple compounds or interventions; combination experiments require explicit components.
- Measurements are linked to **one experiment, one sample group or arm, one endpoint, and one time point**; summarize across arms only in separately typed statistical contrasts.
- Source anchors can reference a text passage, figure, panel, table, supplementary file, or direct dataset row.
- Mechanism graph edges require explicit context and evidence provenance, never just a language model's conjecture.

## 3. General field conventions

| Parameter | Definition | Type / rule |
|---|---|---|
| `id` | Stable internal entity identifier | UUID or namespaced string |
| `schema_version` | Version of field contract | Semantic version string |
| `created_at`, `updated_at` | Ingestion and modification timestamps | ISO 8601 UTC |
| `extractor_version` | Code/model prompt used for parsing | Versioned string |
| `curation_status` | Lifecycle of extracted record | `raw`, `machine_extracted`, `needs_review`, `verified`, `rejected`, `superseded` |
| `reviewer_id` | Scientific curator identifier | Internal pseudonymous ID; nullable |
| `reviewed_at` | Scientific review timestamp | ISO 8601 UTC; nullable |
| `missing_reason` | Reason a scientifically relevant field is absent | `not_reported`, `not_applicable`, `not_accessible`, `ambiguous`, `extraction_failed`, `pending_review` |
| `source_anchor_ids` | Traceable source locations for assertion | Array of IDs, mandatory for verified claims |

Do not use free-text strings for controlled vocabularies where a standardized ontology/code is available. Preserve an `original_text` alongside a normalized field.

## 4. Publication parameters

| Field | Meaning | Format / validation |
|---|---|---|
| `publication_id` | Unique study/publication identifier | Internal ID |
| `doi` | DOI of publication | DOI string, nullable, deduplicated |
| `pmid`, `pmcid` | PubMed identifiers | Strings, nullable |
| `title` | Exact published title | Text |
| `authors` | List of named authors | Structured list |
| `year` | Publication year | Integer |
| `journal` | Journal or publication venue | Text |
| `publication_type` | Experimental article, systematic review, narrative review, preprint, dataset, etc. | Controlled enum |
| `peer_review_status` | Peer-reviewed, preprint, unknown | Controlled enum |
| `publication_date` | Original publication date | ISO 8601 date, nullable |
| `version` | Version/correction/retraction status | Text plus external ID |
| `url` | Canonical source URL | HTTPS URL |
| `license` | Reuse license and restrictions | SPDX if possible; otherwise source-specific |
| `full_text_access` | Whether text was accessible for extraction | `abstract`, `open_full_text`, `licensed_full_text`, `user_supplied`, `unavailable` |
| `dataset_links` | Supplementary/raw data references | Array of URLs/IDs |
| `funding`, `conflicts_of_interest` | Disclosed funding/COI | Text or structured records |
| `source_role` | How paper is used | `primary_measurement`, `review_discovery`, `method_reference` |

**Rule:** never treat a review's paraphrase as a primary numeric measurement when the underlying experiment can be retrieved.

## 5. Research-question and hypothesis parameters

| Field | Meaning | Format / validation |
|---|---|---|
| `question_id` | Stable research-question ID | Internal ID |
| `publication_id` | Source publication | Foreign key |
| `question_text` | Question as stated or inferred | Text |
| `question_origin` | Was it quoted from author or inferred? | `explicit`, `inferred` |
| `exact_author_text` | Exact text when explicitly stated and licensable | Text / bounded excerpt, nullable |
| `question_scope` | Mechanistic, descriptive, causal, dose-response, translation, clinical | Multi-label enum |
| `target_endpoint_ids` | Outcome(s) relevant to question | Array of endpoint IDs |
| `target_model` | Intended biological model | Reference to model context |
| `question_status` | Answered within study, partially supported, unresolved | Controlled enum, reviewer-approved |
| `hypothesis_id` | Hypothesis identifier | Internal ID |
| `hypothesis_text` | Testable prediction | Text |
| `hypothesis_origin` | Explicit vs inferred | `explicit`, `inferred` |
| `predicted_direction` | Expected directional effect | `increase`, `decrease`, `no_change`, `nonmonotonic`, `unknown` |
| `linked_experiment_ids` | Experiments testing hypothesis | Array of IDs |

**Rule:** an inferred question cannot be presented as a direct quote from researchers. Questions are not training labels for biological response prediction.

## 6. Experiment and biological context parameters

| Field | Meaning | Format / validation |
|---|---|---|
| `experiment_id` | Within-paper experimental unit | Internal ID |
| `publication_id` | Parent paper | Foreign key |
| `experiment_label` | e.g., Fig. 2a–c / Experiment 3 | Text |
| `design_type` | Randomized, observational, ex vivo, in vitro, in vivo, clinical, computational | Controlled enum / multiple dimensions |
| `biological_system` | Dissociated culture, brain slice, organoid, animal, human participant, etc. | Controlled ontology |
| `species_common`, `species_taxon_id` | Species and stable taxonomy reference | e.g., mouse / NCBI taxonomy ID |
| `strain_or_line` | Animal strain or cell line | Text, nullable |
| `donor_id`, `donor_count` | Human cell donor metadata without identifiers | Deidentified ID / integer |
| `sex`, `age`, `developmental_stage` | Biological covariates where reported | Categorical, original units, nullable |
| `cell_type_original` | Author's cell-type label | Text |
| `cell_type_standardized` | Standard taxonomy/ontology mapping | Ontology ID plus confidence |
| `brain_region_original`, `brain_region_standardized` | Source region, e.g. frontal cortex / dentate gyrus | Text + atlas ontology |
| `culture_maturity` | Days in vitro or organoid age | Value plus unit |
| `culture_conditions` | Medium, co-culture, seeding density etc. | Structured metadata |
| `batch_id` | Experimental batch | Deidentified string, nullable |
| `randomization` | Randomization performed? | `yes`, `no`, `unclear` |
| `blinding` | Blinding performed? | `yes`, `no`, `unclear` |
| `inclusion_exclusion_criteria` | Subject or sample selection | Text |
| `technical_replicates`, `biological_replicates` | Different repeat types | Nonnegative integers, nullable |
| `control_definition` | Vehicle, untreated, active comparator, etc. | Controlled enum + description |
| `experimental_notes` | Relevant unstructured context | Text |

**Rule:** `species`, `cell_type`, and `model_system` must be independently recorded. A human-derived organoid is not a human clinical study.

## 7. Intervention, dose, and exposure parameters

| Field | Meaning | Format / validation |
|---|---|---|
| `intervention_id` | Exposure identifier | Internal ID |
| `compound_name_original` | Exact author label | Text |
| `compound_normalized_id` | Stable compound identifier | e.g., PubChem CID / ChEBI |
| `chemical_form` | Parent drug, active metabolite, salt, isomer, formulation | Controlled enum + name |
| `intervention_type` | Drug, genetic perturbation, stimulation, behavioral treatment | Controlled enum |
| `dose_original_value` | Numeric value stated by paper | Decimal |
| `dose_original_unit` | Exact stated unit | e.g., `mg/kg`, `µM`, `nM`, `mg`, `µg/mL` |
| `normalized_value`, `normalized_unit` | Optional converted value with rule | Decimal + unit; conversion provenance mandatory |
| `exposure_route` | Oral, i.p., i.v., bath, culture media, etc. | Controlled enum |
| `vehicle` | Solvent/vehicle condition | Text |
| `exposure_start` | Start relative to experiment origin | Numeric offset + unit |
| `exposure_duration` | Exposure duration | Value and unit |
| `regimen` | Single, repeat, pulse, continuous | Enum |
| `exposure_frequency` | Number of administrations/time | Structured |
| `washout_duration` | Time after exposure removal | Value and unit, nullable |
| `comparator_arm_id` | Explicit comparison arm | Foreign key |
| `co_interventions` | Other simultaneous interventions | Array of references |
| `target_concentration_vs_measured` | Nominal vs assayed exposure | Enum |
| `pharmacokinetic_context` | Brain/plasma level data if reported | Structured, nullable |

**Critical dose rules:** Never silently convert `µM` to `mg/kg`, or animal doses to human doses. A conversion between molar and mass concentrations requires verified molecular identity and molecular weight, and is still **not** an administered human-equivalent dose. Keep route and exposure context distinct.

## 8. Temporal and longitudinal parameters

| Field | Meaning | Format / validation |
|---|---|---|
| `time_origin` | What `t=0` means | First dose, culture seeding, surgery, etc. |
| `sample_collection_time` | Time specimen was collected | Relative time + unit |
| `outcome_observation_time` | Time assay was recorded | Relative time + unit |
| `time_since_last_exposure` | Useful for repeated dosing | Duration, nullable |
| `timepoint_type` | Baseline, acute, subacute, long-term follow-up | Enum; keep exact time |
| `repeated_measure_design` | Whether same individual cell/animal was followed | `same_unit`, `independent_cohorts`, `mixed`, `unknown` |
| `longitudinal_unit_id` | Deidentified cell/animal/group tracking ID | Nullable |
| `attrition_n` | Lost units since prior time point | Integer, nullable |
| `persistence_status` | Sustained, returned to baseline, reversed, unclear | Reviewer-coded; endpoint-specific |

**Rule:** Do not plot independent cohorts as if they were paired single-cell trajectories. Do not interpolate or extrapolate unmeasured values as if observed.

## 9. Endpoints and measurable outcome parameters

### 9.1 Common fields for every measurement

| Field | Meaning | Format / validation |
|---|---|---|
| `measurement_id` | Unique measurement record | Internal ID |
| `endpoint_id` | Target phenotype/measurement definition | Foreign key |
| `endpoint_label_original` | Exact label in publication | Text |
| `endpoint_normalized` | Standardized scientific concept | Ontology/code + mapping provenance |
| `measurement_scale` | Molecular, cellular, synaptic, circuit, behavioral, clinical | Enum |
| `assay_method` | Microscope, imaging, electrophysiology, qPCR, etc. | Controlled code + description |
| `assay_protocol` | Reference/protocol details | URL/text |
| `instrument`, `analysis_software` | Measurement devices and pipeline | Versioned strings, nullable |
| `region_of_interest` | Sampled field or anatomical region | Structured |
| `arm_id`, `sample_group_id` | Group producing result | Foreign keys |
| `observation_time` | When measured relative to intervention | Value/unit + reference |
| `raw_value` | Reported observation | Decimal or vector/table reference |
| `raw_unit` | Reported unit | UCUM-compatible where feasible |
| `control_value`, `control_unit` | Comparator measurement | Decimal and unit; nullable |
| `effect_direction` | Increase, decrease, no change, mixed | Enum |
| `effect_size_type` | Absolute difference, ratio, percent change, standardized mean difference | Enum |
| `effect_size_value` | Numeric effect | Decimal |
| `sample_size_n` | Number of independent biological units | Integer; see statistical unit |
| `independent_unit` | Cell, animal, donor, culture well, participant | Enum |
| `uncertainty_type` | SD, SEM, CI, IQR, bootstrap, none | Enum |
| `uncertainty_value` | Numeric uncertainty | Decimal or interval |
| `statistical_test`, `p_value`, `multiple_testing_correction` | Inferential metadata | Structured |
| `image_or_raw_data_uri` | Source data location | URL and license |
| `is_imputed`, `is_derived` | Derived rather than reported | Boolean |
| `extraction_method` | Direct table, direct text, image digitization, model-derived | Enum |
| `source_anchor_ids` | Exact figure/table/text source | Nonempty list for verified measurements |

### 9.2 Endpoint taxonomy

| Scale | Endpoint examples | Preferred units / notes |
|---|---|---|
| Molecular | BDNF abundance; TrkB phosphorylation; mTOR activity; Arc/c-Fos expression | Relative fold-change, normalized abundance, concentration; specify normalization |
| Cellular | Neurite length; Sholl intersection counts; dendritic branch points; cell viability | µm, count, intersections/radius, %, with analysis protocol |
| Neurogenesis | BrdU+/NeuN+ cell counts; proliferation markers; survival of newborn neurons | Counts per region/area; distinguish proliferation vs differentiation vs survival |
| Synaptic structural | Spine density; spine size; spine formation rate; elimination rate; survival/stabilization | Spines/µm, volume/area proxy, fraction per time, survival probability |
| Synaptic functional | EPSC amplitude/frequency; plasticity measures | pA, Hz, fold change; specified recording conditions |
| Circuit/network | Firing rates; functional connectivity, calcium-event synchrony; EEG/fMRI measures | Hz or method-specific; specify calculation and preprocessing |
| Behavioral | Freezing percentage; extinction learning; locomotion | %, time, task-defined score with procedure |
| Clinical | Validated symptom scores; safety outcomes | Named scale, scoring direction, cohort characteristics |

**Structural remodeling rule:** For spine studies, capture `new_spines`, `eliminated_spines`, `surviving_spines`, `formation_rate`, `elimination_rate`, `survival_rate`, `net_density`, and their sampling window **as separate measures** where reported.

**Mechanistic interpretation rule:** changes in BDNF/TrkB or receptor expression are not direct evidence of a change in human memory or disease outcome.

## 10. Mechanism knowledge graph parameters

### Node fields
`mechanism_node_id`, `node_type` (`compound`, `receptor`, `protein`, `gene`, `pathway`, `cell_type`, `brain_region`, `process`, `endpoint`), `canonical_name`, `ontology_id`, `aliases`, `species_context`, `source_anchor_ids`.

### Edge fields

| Field | Meaning | Format |
|---|---|---|
| `edge_id` | Stable graph relation | Internal ID |
| `subject_node_id`, `object_node_id` | Graph endpoints | Foreign keys |
| `predicate` | Activates, inhibits, binds, associated_with, required_for, sufficient_for, modulates | Controlled list |
| `claim_direction` | Positive, negative, mixed, unknown | Enum |
| `evidence_class` | Direct binding assay, pharmacological blockade, genetic perturbation, correlation, review hypothesis, computational prediction | Controlled enum |
| `causal_status` | Intervention-supported, associative, proposed | Enum |
| `supporting_experiment_id` | Original experiment | Nullable, required for primary evidence |
| `supporting_measurement_ids` | Measurements backing edge | Array |
| `model_context_id` | Species/cell/assay context | Required |
| `dose_exposure_id`, `observation_time` | Intervention condition | Nullable but retained if relevant |
| `source_anchor_ids` | Exact source support | Required |
| `conflicting_edge_ids` | Contradictory evidence to review | Array |
| `human_review_status` | Approval workflow | Enum |

**Never infer that a mechanistic relationship is universal based on one cell model.** For example, blockade with ketanserin supports receptor involvement under those conditions, not necessarily exclusivity across contexts.

## 11. Evidence assessments and contradiction parameters

### Evidence assessment dimensions
- `design_quality`: control selection, randomization, blinding, and pre-registration when relevant.
- `measurement_validity`: assay suitability, reproducibility, endpoint specificity, quality control.
- `statistical_support`: effect size, intervals, unit of analysis, multiplicity, and sample size.
- `independent_replication`: number/quality of independent laboratories or datasets.
- `directness`: whether the endpoint is directly measured or proxied.
- `translation_relevance`: match to requested species, cell type, age/maturity, route, and exposure.
- `completeness`: accessible raw data, full methods, and missing fields.
- `limitations_text`: curator note and author-reported caveats.

**Avoid one opaque global confidence score.** Show evidence dimensions and the reason for each rating, with `unknown` allowed.

### Contradiction record
`comparison_id`, `source_measurement_a`, `source_measurement_b`, `apparent_disagreement_type`, `same_endpoint_boolean`, `same_assay_boolean`, `dose_comparable_boolean`, `time_comparable_boolean`, `model_comparable_boolean`, `statistical_compatibility`, `potential_explanations`, `reviewer_verdict` (`real_conflict`, `contextual_difference`, `insufficient_information`, `no_conflict`), `source_anchor_ids`.

A null effect and a significant effect do not alone prove that two studies conflict; compare effect estimates and intervals.

## 12. Cross-species / cross-model comparison parameters

| Field | Definition |
|---|---|
| `source_experiment_id`, `target_experiment_id` | Compared studies |
| `source_species`, `target_species` | Explicit source and target |
| `source_model`, `target_model` | Animal in vivo, human-derived neurons, organoids, clinical, etc. |
| `cell_type_mapping` | Biological correspondence with ontology and evidence |
| `gene_orthology_mapping` | Explicit homolog/ortholog mapping when used |
| `assay_match_level` | Same, similar, incompatible, unknown |
| `endpoint_match_level` | Same, harmonizable, indirect proxy, incompatible |
| `compound_equivalence` | Same compound/form/metabolite, different, unknown |
| `dose_exposure_compatibility` | Same units/route? PK/exposure evidence? |
| `temporal_compatibility` | Time point, sampling schedule, longitudinal design |
| `translation_constraints` | Caveats and unmeasured confounders |
| `model_prediction` | Separate predicted value and unit, only after validation |
| `prediction_interval` | Interval with known calibration and held-out benchmark |
| `domain_of_applicability` | Explicit included species/cell/assay/dose/time regions |
| `abstention_reason` | Why no supported prediction is issued |

A human-derived culture prediction is not a human clinical outcome prediction.

## 13. Source anchors and provenance

| Field | Meaning |
|---|---|
| `anchor_id` | Unique source location |
| `publication_id` | Source publication |
| `source_type` | Abstract, full-text section, figure panel, table row, supplement, external data |
| `section_title`, `page_number` | Where found |
| `figure_number`, `panel_label`, `table_number`, `row_key` | Exact data reference |
| `quote_excerpt` | Permitted short source excerpt, if license allows |
| `source_url`, `file_hash` | Content location and version |
| `extraction_timestamp`, `extraction_model_version` | Provenance of extraction |
| `reviewed_by`, `review_timestamp` | Who verified the source correspondence |
| `correction_history` | Audit log |

Keep separate `author_reported`, `extracted`, `unit_converted`, `digitized_from_plot`, `statistically_derived`, and `predicted` value origins.

## 14. Missing data, units and normalization

- Store all original values and units **unchanged**.
- Normalize units only when physically and scientifically meaningful; record exact formula, molecular identity, precision, and conversion code version.
- Preserve ranges, approximate values, detection limits, `p < ...` reporting, and censored measurements rather than substituting arbitrary exact numbers.
- For mean ± error bar, identify SD vs SEM vs CI. Do not automatically convert unless `n` and assumptions are known.
- Distinguish biological from technical replicates to avoid pseudoreplication.
- Record reporting of dose per body mass separately from achieved brain/cell exposure.
- Use explicit missingness indicators; missing human studies ≠ negative human result.

### v0 core normalization (core-0.3.0, extended in core-0.4.0)

Free-text fields that the comparison logic depends on are now checked by the schema, so the same thing is always written the same way. Only spelling is normalized; no value is converted.

| Field | Rule | Why |
|---|---|---|
| `measurement.time_unit` | One of `seconds`, `minutes`, `hours`, `days`, `weeks`, `months`, `years`. Common variants (`day`, `hr`, `wk`, `nights`) are mapped to these on load; anything else is rejected. | `day` and `days` were stored as different units, so the same time basis was flagged as different. |
| `measurement.endpoint_normalized` | Required snake_case key. If extraction gives none, it is derived from `endpoint_original`. | Comparison and gap counts group by this key; a missing key silently split one outcome into several. |
| `experiment.species` | Lower-cased on load. | Avoids `Mouse` vs `mouse` mismatches. |

**core-0.4.0: any intervention.** `arm.intervention_type` is one of `substance`, `exercise`, `sleep`, `meditation`, `diet`, `environment`, `other` (default `substance`). A non-substance arm has no chemical dose: leave `dose_value` empty with the reason `not_applicable` and put the protocol in `regimen`, which is then required. Never force sleep or exercise into dose fields. Which interventions are collected is set in [config/interventions.json](../config/interventions.json), not in code.

Dose units, value units and `time_origin` stay as the authors wrote them. The time **value** is never converted (7 days is not rewritten as 1 week). After any schema change, run `pipeline/migrate_evidence.py`: it re-validates every stored row, refuses to write if any row fails, and bumps `schema_version`.

## 15. Example structured record (illustrative schema only)

```json
{
  "publication": {
    "publication_id": "pub_example_001",
    "doi": "example-doi",
    "publication_type": "primary_experimental",
    "source_role": "primary_measurement"
  },
  "research_questions": [
    {
      "question_id": "rq_001",
      "question_text": "Does intervention X alter dendritic spine dynamics?",
      "question_origin": "inferred"
    }
  ],
  "experiments": [
    {
      "experiment_id": "exp_001",
      "biological_system": "animal_in_vivo",
      "species_common": "mouse",
      "cell_type_original": "cortical pyramidal neuron",
      "brain_region_original": "frontal cortex",
      "interventions": [
        {
          "intervention_id": "int_001",
          "compound_name_original": "Compound X",
          "dose_original_value": null,
          "dose_original_unit": null,
          "exposure_route": "not_reported"
        }
      ],
      "measurements": [
        {
          "measurement_id": "meas_001",
          "endpoint_normalized": "dendritic_spine_formation_rate",
          "observation_time": {"value": 7, "unit": "days"},
          "raw_value": null,
          "raw_unit": "fraction_per_day",
          "missing_reason": "not_reported",
          "curation_status": "needs_review",
          "source_anchor_ids": []
        }
      ]
    }
  ]
}
```

This record is **fictional** and demonstrates shape/missingness only. It must not appear in scientific result charts or model training.

## 16. Extraction and review pipeline

1. **Discover** relevant publications using publication metadata and manually verified inclusion criteria.
2. **Check access and licenses** before ingesting full text or supplements.
3. **Parse** sections, tables, figure captions, and supplemental datasets where permissible.
4. **Extract** publication/question/hypothesis/experiment/arm/endpoint/measurement into typed candidate JSON.
5. **Normalize cautiously** with deterministic units and ontology matching, retaining originals.
6. **Check schema** for missing critical variables, impossible units, duplicates, ambiguous compound identities, and sampling inconsistencies.
7. **Verify provenance** down to figure/table/span; flag unsupported extracted claims.
8. **Expert review** by independent curator; resolve ambiguities and record corrections.
9. **Publish versioned evidence** with per-record status and license.
10. **Evaluate** accuracy periodically against a blinded gold-standard set.

Use reviewer adjudication for disagreements and measure inter-annotator agreement.

## 17. Dataset splits and future model training

### Training-ready minimum
A validated record needs endpoint definition, comparable biological model/cell identity, intervention identity and exposure, time, assay and units, comparator, numerical target, statistical unit, data origin, and source proof.

### Split policy
- Hold out entire **publications and laboratories** to prevent leakage.
- Also test intervention-held-out and cell-context-held-out splits where feasible.
- For time prediction, test genuinely held-out measurement times.
- For cross-species modeling, assess on human-derived observations excluded from training and tuning.
- Deduplicate shared figure data appearing across papers and reviews.
- Avoid mixing repeated measurements of the same biological unit across train and test.

### Evaluation
- Extraction: precision, recall, numeric/unit exactness, citation fidelity, review burden.
- Graph: relation accuracy, causal-status errors, source match.
- Contradictions: expert-agreed precision/recall and explanatory accuracy.
- Prediction: MAE/RMSE or endpoint-appropriate scores, baseline comparison, interval coverage and calibration, performance by model/cell/lab, and abstention/selective risk.
- Scientific utility: prospectively tested experiment-prioritization value, not only offline prediction.

## 18. Sources, licensing, privacy and governance

**Candidate sources:** PubMed, Europe PMC, original articles/supplements, NeuroMorpho.Org, Allen Brain Cell Atlas, ModelDB, Brain Image Library, compatible perturbation and microscopy repositories.

**Source roles:** `primary experimental ground truth`, `reference data`, `mechanistic model`, `review/discovery`, `illustrative content`.

The OPEN Foundation article (https://open-foundation.org/psilocybin-and-neuroplasticity/) is a **secondary overview** and reference discovery resource; extract actual numeric outcomes from the cited experimental studies wherever possible.

**Governance controls:**
- respect repository and publisher licenses; do not indiscriminately archive restricted full texts;
- keep private partner research isolated and access-controlled;
- de-identify human donors/participants and avoid protected health information unless a separately approved workflow exists;
- maintain source versioning, correction/retraction flags, audit logs, and deletion/retention policy;
- prohibit clinical decision support and personalized psychedelic dosage recommendations in the research MVP.

## 19. MVP implementation sequence and data readiness gates

### Gate 1 — Ontology and schema
Define controlled vocabularies for organism, experimental model, neuronal subtype, brain region, route, endpoint, assay, intervention identity, and evidence class. Manually encode 5 test papers to stress-test schema cardinality.

### Gate 2 — Gold-standard extraction
Build 15–25 deeply curated papers with research questions, experiments, arms, outcomes, and source anchors. Measure accuracy by field; evaluate source traceability.

### Gate 3 — Mechanism and contradiction graph
Add experimentally supported edges and apparent-conflict candidates. Require scientific adjudication of each causal edge and contradiction.

### Gate 4 — Scale evidence database
Expand toward 50–100 compatible papers while maintaining quality controls. Build observed dose/time charts and evidence gaps.

### Gate 5 — Predictive feasibility
Audit whether one endpoint has sufficient comparable measured results across doses/time/models and at least one independent external test. If not, stop predictive work and keep delivering research workflow value.

## 20. Open design decisions for neuroscientist review

1. Which *single* endpoint and assay should define the first validated release?
2. What source ontologies should standardize human/mouse neuronal subtypes and anatomy?
3. When do two reported morphology measurements count as comparable?
4. Which evidence types justify “causal” versus “associated” graph relations?
5. What is the smallest useful gold-standard extraction set, with tolerable scientific error?
6. Which high-value datasets have permissions and sufficient raw measurements?
7. How should conflicting studies be displayed without a misleading composite confidence score?
8. What biological context defines a valid domain of applicability for any predictor?

---

**Implementation decision:** Ship the evidence schema and curator workflow first. The full mechanism graph and prediction capabilities should be phased and validated independently. No model should invent or extrapolate a human-cell outcome without appropriate test data.
