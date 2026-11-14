import "server-only";
import fs from "node:fs";
import path from "node:path";
import type { EvidenceRow, Publication } from "./types";

// Data produced by ../pipeline. Read-only: the UI never writes records.
const DATA_DIR = process.env.DATA_DIR ?? path.resolve(process.cwd(), "..", "data");
const EVIDENCE_FILE = process.env.EVIDENCE_FILE ?? path.join(DATA_DIR, "evidence", "evidence_rows.jsonl");

const CONFIG_FILE = process.env.INTERVENTIONS_FILE ?? path.resolve(DATA_DIR, "..", "config", "interventions.json");

export interface Intervention {
  name: string;
  /** substance, exercise, sleep, meditation, diet, environment, other */
  type: string;
  /** Label shown in the UI; defaults to the name. */
  display: string;
}

interface InterventionConfig { name: string; type?: string; display?: string; members?: string[] }

function interventionConfig(): InterventionConfig[] {
  if (!fs.existsSync(CONFIG_FILE)) return [];
  return (JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8")).interventions ?? []) as InterventionConfig[];
}

/**
 * The interventions to show: everything in config/interventions.json, plus any other
 * intervention a corpus paper is tagged with. Nothing in the UI names a compound.
 */
export function interventions(): Intervention[] {
  const out = new Map<string, Intervention>();
  for (const c of interventionConfig())
    out.set(c.name, { name: c.name, type: c.type ?? "substance", display: c.display ?? c.name });
  for (const p of corpus())
    for (const s of p.extended.corpus?.substances ?? [])
      if (!out.has(s)) out.set(s, { name: s, type: "substance", display: s });
  return [...out.values()];
}

/** Maps an arm's intervention to the entry it is shown under (e.g. a prodrug's active form). */
export function interventionGrouper(): (name: string) => string {
  const group = new Map<string, string>();
  for (const c of interventionConfig())
    for (const m of [c.name, ...(c.members ?? [])]) group.set(m.trim().toLowerCase(), c.name);
  return (name) => group.get(name.trim().toLowerCase()) ?? name;
}

/** True when EVIDENCE_FILE points at a test fixture instead of pipeline output. */
export const isFixture = process.env.EVIDENCE_FIXTURE === "1";

function readJsonl<T>(file: string): T[] {
  if (!fs.existsSync(file)) return [];
  return fs.readFileSync(file, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l) as T);
}

export function corpus(): Publication[] {
  return readJsonl<Publication>(path.join(DATA_DIR, "papers", "corpus.jsonl"));
}

export function publication(id: string): Publication | undefined {
  return corpus().find((p) => p.publication_id === id);
}

/** Only rows that belong to a corpus paper; anything else is ignored. */
export function evidenceRows(): EvidenceRow[] {
  const ids = new Set(corpus().map((p) => p.publication_id));
  return readJsonl<EvidenceRow>(EVIDENCE_FILE).filter((r) => ids.has(r.publication_id));
}

export function rowsFor(publicationId: string): EvidenceRow[] {
  return evidenceRows().filter((r) => r.publication_id === publicationId);
}

export function row(id: string): EvidenceRow | undefined {
  return evidenceRows().find((r) => r.evidence_id === id);
}

export function rowsByIds(ids: string[]): EvidenceRow[] {
  const all = new Map(evidenceRows().map((r) => [r.evidence_id, r]));
  return ids.map((id) => all.get(id)).filter((r): r is EvidenceRow => Boolean(r));
}

export interface PipelineStats {
  discovered: number;
  /** References from the direct PubMed/Europe PMC search (pipeline/search_literature.py). */
  searched: number;
  resolved: number;
  excluded: Record<string, number>;
  unresolved: number;
}

export function pipelineStats(): PipelineStats {
  const excl = readJsonl<{ exclusion_code: string }>(path.join(DATA_DIR, "papers", "exclusions.jsonl"));
  const excluded: Record<string, number> = {};
  for (const e of excl) excluded[e.exclusion_code] = (excluded[e.exclusion_code] ?? 0) + 1;
  return {
    discovered: readJsonl(path.join(DATA_DIR, "discovery", "open_posts.jsonl")).length,
    searched: readJsonl(path.join(DATA_DIR, "discovery", "literature_search.jsonl")).length,
    resolved: readJsonl(path.join(DATA_DIR, "papers", "papers.jsonl")).length,
    excluded,
    unresolved: readJsonl(path.join(DATA_DIR, "papers", "unresolved.jsonl")).length,
  };
}

export interface Screening {
  publication_id: string;
  pmcid: string;
  reports_measured_outcomes: boolean;
  reason: string;
  model: string;
}

/** Per-paper screening decisions written by pipeline/extract.py. */
export function screening(): Screening[] {
  return readJsonl<Screening>(path.join(DATA_DIR, "evidence", "screening.jsonl"));
}
