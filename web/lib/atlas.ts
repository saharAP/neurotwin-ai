import "server-only";
import fs from "node:fs";
import path from "node:path";
import { corpus, evidenceRows, interventionGrouper, interventions, screening } from "./data";
import { doseText, shortCite, timeText } from "./format";
import { evidenceLevel } from "./levels";
import type { EvidenceRow } from "./types";

// The Neuron Outcome Atlas view of the evidence rows (docs/MVP_V0.md §3-§8).
// The endpoint registry is config/endpoints.json: a row belongs to the atlas only if its
// endpoint key is listed under a registry endpoint. Nothing here pools studies.

const DATA_DIR = process.env.DATA_DIR ?? path.resolve(process.cwd(), "..", "data");
const REGISTRY_FILE = process.env.ENDPOINTS_FILE ?? path.resolve(DATA_DIR, "..", "config", "endpoints.json");

export type Visual = "neurogenesis" | "spines" | "branching" | "survival" | null;
export interface Endpoint { id: string; label: string; aliases: string[] }
export interface Outcome {
  id: string; label: string; short: string; description: string; visual: Visual; endpoints: Endpoint[];
}
export interface Registry { status: string; outcomes: Outcome[]; context_markers: Endpoint[] }

export function registry(): Registry {
  if (!fs.existsSync(REGISTRY_FILE)) return { status: "missing", outcomes: [], context_markers: [] };
  return JSON.parse(fs.readFileSync(REGISTRY_FILE, "utf8")) as Registry;
}

/** How the percent change was obtained. It is always against the study's own comparator. */
export type PctBasis = "reported" | "from_fold" | "from_values";

export interface Contrast {
  id: string;
  pubId: string;
  cite: string;
  outcomeId: string;
  endpointId: string;
  endpointLabel: string;
  endpointOriginal: string;
  /** Column the row is shown under (a prodrug is grouped with its active form). */
  intervention: string;
  /** What the arm actually received, as recorded. */
  compound: string;
  armLabel: string;
  dose: string;
  species: string;
  level: string;
  model: string;
  region: string | null;
  time: string;
  value: number | null;
  control: number | null;
  unit: string | null;
  uncertainty: string | null;
  n: number | null;
  nUnit: string;
  direction: string;
  pct: number | null;
  pctBasis: PctBasis | null;
  p: string | null;
  assay: string | null;
  comparator: string;
  /** Mechanism probe given with the intervention (e.g. a receptor blocker), or null. */
  probe: string | null;
  quote: string;
  quoteWhere: string;
  verified: boolean;
  agreement: string;
}

/**
 * Percent change against the study's own comparator.
 * - "reported": the paper states a percent difference or change itself.
 * - "from_fold": the paper states a fold change; (fold - 1) x 100.
 * - "from_values": both group values are reported; (value - control) / control x 100.
 * Returns null when none applies. Nothing is estimated.
 */
export function percentChange(r: EvidenceRow): { pct: number; basis: PctBasis } | null {
  const m = r.measurement;
  if (m.value === null) return null;
  const unit = (m.value_unit ?? "").toLowerCase();
  if (/% (difference|change|increase|decrease)/.test(unit)) return { pct: m.value, basis: "reported" };
  if (/fold/.test(unit)) return { pct: (m.value - 1) * 100, basis: "from_fold" };
  if (m.control_value !== null && m.control_value > 0)
    return { pct: ((m.value - m.control_value) / m.control_value) * 100, basis: "from_values" };
  return null;
}

function uncertaintyText(r: EvidenceRow): string | null {
  const m = r.measurement;
  if (m.uncertainty_type === "none_reported" || m.uncertainty_low === null) return null;
  if (m.uncertainty_type === "SD" || m.uncertainty_type === "SEM") return `± ${m.uncertainty_low} ${m.uncertainty_type}`;
  return `[${m.uncertainty_low}, ${m.uncertainty_high}] ${m.uncertainty_type}`;
}

export interface AtlasData {
  registry: Registry;
  contrasts: Contrast[];
  /** Rows on context markers (BDNF and similar): kept, counted, not part of the five outcomes. */
  contextMarkers: { id: string; label: string; rows: number; studies: number }[];
  /** Rows on other endpoints (behavioral, clinical, circuit...): kept as context only. */
  otherRows: number;
  totalRows: number;
}

export function atlas(): AtlasData {
  const reg = registry();
  const byAlias = new Map<string, { outcome: Outcome; endpoint: Endpoint }>();
  for (const o of reg.outcomes)
    for (const e of o.endpoints)
      for (const a of e.aliases) byAlias.set(a, { outcome: o, endpoint: e });
  const markerByAlias = new Map<string, Endpoint>();
  for (const e of reg.context_markers) for (const a of e.aliases) markerByAlias.set(a, e);

  const pubs = new Map(corpus().map((p) => [p.publication_id, p]));
  const group = interventionGrouper();
  const rows = evidenceRows();
  const contrasts: Contrast[] = [];
  const markerRows = new Map<string, EvidenceRow[]>();
  let other = 0;

  for (const r of rows) {
    const m = r.measurement;
    const hit = byAlias.get(m.endpoint_normalized);
    if (!hit) {
      const marker = markerByAlias.get(m.endpoint_normalized);
      if (marker) markerRows.set(marker.id, [...(markerRows.get(marker.id) ?? []), r]);
      else other += 1;
      continue;
    }
    const pub = pubs.get(r.publication_id);
    const pc = percentChange(r);
    const probes = r.preclinical?.probes ?? [];
    const a = r.anchors[0];
    contrasts.push({
      id: r.evidence_id,
      pubId: r.publication_id,
      cite: pub ? shortCite(pub) : r.publication_id,
      outcomeId: hit.outcome.id,
      endpointId: hit.endpoint.id,
      endpointLabel: hit.endpoint.label,
      endpointOriginal: m.endpoint_original,
      intervention: group(r.arm.intervention_normalized),
      compound: r.arm.intervention_normalized,
      armLabel: r.arm.label,
      dose: doseText(r),
      species: r.experiment.species,
      level: evidenceLevel(r.experiment.design, r.experiment.species),
      model: [r.preclinical?.cell_type, r.preclinical?.brain_region].filter(Boolean).join(", ")
        || r.experiment.population_or_model,
      region: r.preclinical?.brain_region ?? null,
      time: m.time_value !== null ? timeText(r) : "time not reported",
      value: m.value,
      control: m.control_value,
      unit: m.value_unit,
      uncertainty: uncertaintyText(r),
      n: r.experiment.n,
      nUnit: r.experiment.independent_unit,
      direction: m.effect_direction,
      pct: pc ? Math.round(pc.pct * 10) / 10 : null,
      pctBasis: pc?.basis ?? null,
      p: m.p_value,
      assay: m.assay_or_instrument,
      comparator: r.arm.comparator_label ?? r.arm.comparator_type.replace(/_/g, " "),
      probe: probes.length ? probes.map((x) => `${x.agent}${x.target ? ` (${x.target})` : ""}`).join(", ") : null,
      quote: a?.quote ?? "",
      quoteWhere: [a?.section, a?.label].filter(Boolean).join(" · "),
      verified: r.anchors.some((x) => x.quote_verified),
      agreement: r.agreement,
    });
  }

  return {
    registry: reg,
    contrasts,
    contextMarkers: reg.context_markers.map((e) => {
      const rs = markerRows.get(e.id) ?? [];
      return { id: e.id, label: e.label, rows: rs.length, studies: new Set(rs.map((r) => r.publication_id)).size };
    }),
    otherRows: other,
    totalRows: rows.length,
  };
}

export interface Column { name: string; display: string; type: string; papers: number; unread: number }

/** Atlas columns: every configured intervention, then any other compound that has atlas rows. */
export function atlasColumns(contrasts: Contrast[]): Column[] {
  const pubs = corpus();
  const read = new Set(screening().map((s) => s.publication_id));
  const cols = new Map<string, Column>();
  const add = (name: string, display: string, type: string) => {
    const mine = pubs.filter((p) => p.extended.corpus?.substances.includes(name));
    cols.set(name, { name, display, type, papers: mine.length,
                     unread: mine.filter((p) => !read.has(p.publication_id)).length });
  };
  for (const i of interventions()) add(i.name, i.display, i.type);
  // A compound tested inside another intervention's paper (e.g. an analog) has no tagged papers
  // of its own: count the studies that measured it.
  for (const c of contrasts) {
    if (cols.has(c.intervention)) continue;
    const studies = new Set(contrasts.filter((x) => x.intervention === c.intervention).map((x) => x.pubId)).size;
    cols.set(c.intervention, { name: c.intervention, display: c.intervention, type: "substance", papers: studies, unread: 0 });
  }
  return [...cols.values()];
}

export function countBy<T>(xs: T[], key: (x: T) => string): [string, number][] {
  const m = new Map<string, number>();
  for (const x of xs) m.set(key(x), (m.get(key(x)) ?? 0) + 1);
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
}

export const fmtPct = (x: number) => `${x > 0 ? "+" : ""}${Math.abs(x) >= 100 ? x.toFixed(0) : x.toFixed(1).replace(/\.0$/, "")}%`;
