// Mirrors pipeline/schema.py (core-0.4.0). Python is the source of truth.

export type TimeUnit = "seconds" | "minutes" | "hours" | "days" | "weeks" | "months" | "years";

export type MissingReason =
  | "not_reported" | "not_applicable" | "not_accessible" | "ambiguous"
  | "extraction_failed" | "pending_review";

export interface RecordMeta {
  schema_version: string;
  pipeline_version: string;
  created_at: string;
  updated_at: string;
  curation_status: string;
}

export interface Author { full_name: string | null; orcid: string | null }

export interface Publication {
  meta: RecordMeta;
  publication_id: string;
  doi: string | null;
  pmid: string | null;
  pmcid: string | null;
  title: string;
  year: number | null;
  journal: string | null;
  publication_type: string;
  peer_review_status: string;
  is_retracted: boolean;
  license: string | null;
  full_text_access: string;
  source_role: string;
  missing_reasons: Record<string, MissingReason>;
  extended: {
    authors?: Author[];
    url?: string;
    publication_date?: string | null;
    funding?: { agency?: string; grant_id?: string; statement?: string }[] | null;
    conflicts_of_interest?: string | null;
    dataset_links?: { type: string; text?: string; file?: string; urls?: string[] }[] | null;
    corrections?: { type: string; id?: string }[];
    corpus?: { substances: string[]; therapeutic_areas: string[]; split: string; screening_status: string };
    fulltext?: { fetch_status: string };
  };
}

export interface SourceAnchor {
  location: string;
  section: string | null;
  label: string | null;
  quote: string;
  quote_verified: boolean;
}

export interface EvidenceRow {
  meta: RecordMeta;
  evidence_id: string;
  publication_id: string;
  experiment: {
    label: string; design: string; species: string; population_or_model: string;
    n: number | null; independent_unit: string;
  };
  arm: {
    label: string; intervention_original: string; intervention_normalized: string;
    intervention_type: string;
    dose_value: number | null; dose_unit: string | null; route: string | null;
    regimen: string | null; comparator_label: string | null; comparator_type: string;
  };
  measurement: {
    endpoint_original: string; endpoint_normalized: string; scale_level: string;
    assay_or_instrument: string | null; time_value: number | null; time_unit: TimeUnit | null;
    time_origin: string | null; value: number | null; value_unit: string | null;
    control_value: number | null; effect_direction: string; effect_size_type: string | null;
    effect_size_value: number | null; uncertainty_type: string; uncertainty_low: number | null;
    uncertainty_high: number | null; statistical_test: string | null; p_value: string | null;
    value_origin: string;
  };
  anchors: SourceAnchor[];
  clinical: {
    scale_name: string | null; higher_score_means: string | null;
    responder_rate: number | null; remission_rate: number | null;
    response_definition: string | null; blinding_integrity_assessed: string | null;
    follow_up: string | null;
    adverse_events: { name: string; arm_label: string; n_participants_with_event: number | null;
                      n_participants_in_arm: number | null; severity: string | null }[];
  } | null;
  preclinical?: {
    cell_type: string | null; brain_region: string | null;
    culture_age_value: number | null; culture_age_unit: string | null;
    animal_age: string | null; sex: string | null; strain_or_line: string | null;
    probes: { agent: string; target: string | null; probe_type: string; dose_value: number | null;
              dose_unit: string | null; effect_on_response: string | null }[];
  } | null;
  extended?: Record<string, unknown>;
  extraction_pass: string;
  agreement: "pending" | "ai_consistent" | "ai_disputed" | "single_pass";
  missing_reasons: Record<string, MissingReason>;
}

export const HUMAN_DESIGNS = new Set([
  "randomized_controlled_trial", "nonrandomized_trial", "open_label_trial",
  "observational", "case_report_or_series", "survey",
]);
