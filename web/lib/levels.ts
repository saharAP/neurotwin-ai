// The five evidence levels from docs/MVP_V0.md §3. They are shown side by side
// and never merged: not on the map, not in comparisons.

export type EvidenceLevel =
  | "in vitro"
  | "animal in vivo"
  | "human-derived cells/organoids"
  | "human trial"
  | "human observational"
  | "other";

const BY_DESIGN: Record<string, EvidenceLevel> = {
  in_vitro: "in vitro",
  ex_vivo: "in vitro",
  animal_in_vivo: "animal in vivo",
  organoid: "human-derived cells/organoids",
  randomized_controlled_trial: "human trial",
  nonrandomized_trial: "human trial",
  open_label_trial: "human trial",
  observational: "human observational",
  survey: "human observational",
  case_report_or_series: "human observational",
};

export const LEVEL_ORDER: EvidenceLevel[] = [
  "human trial", "human observational", "human-derived cells/organoids",
  "animal in vivo", "in vitro", "other",
];

export function evidenceLevel(design: string, species?: string): EvidenceLevel {
  // A culture of human cells is a human-derived model, not a human study.
  if (design === "in_vitro" && species?.toLowerCase() === "human") return "human-derived cells/organoids";
  return BY_DESIGN[design] ?? "other";
}
