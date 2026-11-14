import type { EvidenceRow, Publication } from "./types";

export const label = (s: string | null | undefined) => (s ? s.replace(/_/g, " ") : "—");

export function citation(p: Publication): string {
  const authors = p.extended.authors ?? [];
  const first = authors[0]?.full_name ?? "Unknown author";
  const who = authors.length > 2 ? `${first} et al.` : authors.map((a) => a.full_name).join(", ") || first;
  return `${who} (${p.year ?? "n.d."}). ${p.title} ${p.journal ?? ""}.${p.doi ? ` https://doi.org/${p.doi}` : ""}`;
}

export function shortCite(p: Publication): string {
  const last = p.extended.authors?.[0]?.full_name?.split(" ")[0] ?? "Unknown";
  return `${last}${(p.extended.authors?.length ?? 0) > 1 ? " et al." : ""} ${p.year ?? ""}`.trim();
}

export function valueText(r: EvidenceRow): string {
  const m = r.measurement;
  if (m.value === null) return `not reported (${r.missing_reasons["measurement.value"] ?? "missing"})`;
  let s = `${m.value} ${m.value_unit ?? ""}`.trim();
  if (m.uncertainty_type === "SD" || m.uncertainty_type === "SEM") {
    if (m.uncertainty_low !== null) s += ` ± ${m.uncertainty_low} (${m.uncertainty_type})`;
  } else if (m.uncertainty_type !== "none_reported" && m.uncertainty_low !== null) {
    s += ` [${m.uncertainty_low}, ${m.uncertainty_high}] (${m.uncertainty_type})`;
  }
  return s;
}

export function doseText(r: EvidenceRow): string {
  const a = r.arm;
  if (a.dose_value === null) return a.intervention_normalized === "none" ? "—" : "dose not reported";
  return `${a.dose_value} ${a.dose_unit}${a.route ? `, ${a.route}` : ""}`;
}

/** "1 day", "5 weeks". Units are canonical plurals since core-0.3.0; the value is never converted. */
export function timeLabel(value: number, unit: string | null): string {
  if (!unit) return String(value);
  return `${value} ${value === 1 ? unit.replace(/s$/, "") : unit}`;
}

export function timeText(r: EvidenceRow): string {
  const m = r.measurement;
  if (m.time_value === null) return "time not reported";
  return `${timeLabel(m.time_value, m.time_unit)} after ${m.time_origin}`;
}

export const LIMITATIONS = [
  "Research use only. Not medical advice, dosing guidance or a treatment recommendation.",
  "All records are AI-extracted and not expert-reviewed. Check every value against its source quote.",
  "The corpus contains papers reachable from OPEN Foundation's coverage plus one PubMed/Europe PMC search, not a systematic search of all evidence.",
  "Cell-culture, organoid and animal findings are not evidence about the living human brain.",
  "Values are author-reported in original units. No doses are converted across species or units.",
  "A null or missing result is not evidence of no effect or of safety.",
  "Increase or decrease is not the same as benefit or harm.",
];
