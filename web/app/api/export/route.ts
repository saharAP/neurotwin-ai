import { atlas, percentChange } from "@/lib/atlas";
import { corpus, isFixture, rowsByIds } from "@/lib/data";
import { citation, LIMITATIONS } from "@/lib/format";
import type { EvidenceRow } from "@/lib/types";

export const dynamic = "force-dynamic";

const COLUMNS: [string, (r: EvidenceRow) => unknown][] = [
  ["evidence_id", (r) => r.evidence_id],
  ["publication_id", (r) => r.publication_id],
  ["doi", () => ""], // filled below
  ["experiment_design", (r) => r.experiment.design],
  ["species", (r) => r.experiment.species],
  ["population_or_model", (r) => r.experiment.population_or_model],
  ["n", (r) => r.experiment.n],
  ["independent_unit", (r) => r.experiment.independent_unit],
  ["arm", (r) => r.arm.label],
  ["intervention_original", (r) => r.arm.intervention_original],
  ["dose_value_original", (r) => r.arm.dose_value],
  ["dose_unit_original", (r) => r.arm.dose_unit],
  ["route", (r) => r.arm.route],
  ["comparator_type", (r) => r.arm.comparator_type],
  ["endpoint_original", (r) => r.measurement.endpoint_original],
  ["endpoint_normalized", (r) => r.measurement.endpoint_normalized],
  ["scale_level", (r) => r.measurement.scale_level],
  ["time_value", (r) => r.measurement.time_value],
  ["time_unit", (r) => r.measurement.time_unit],
  ["time_origin", (r) => r.measurement.time_origin],
  ["value", (r) => r.measurement.value],
  ["value_unit", (r) => r.measurement.value_unit],
  ["control_value", (r) => r.measurement.control_value],
  ["effect_direction", (r) => r.measurement.effect_direction],
  ["effect_size_type", (r) => r.measurement.effect_size_type],
  ["effect_size_value", (r) => r.measurement.effect_size_value],
  ["uncertainty_type", (r) => r.measurement.uncertainty_type],
  ["uncertainty_low", (r) => r.measurement.uncertainty_low],
  ["uncertainty_high", (r) => r.measurement.uncertainty_high],
  ["p_value", (r) => r.measurement.p_value],
  ["value_origin", (r) => r.measurement.value_origin],
  ["agreement", (r) => r.agreement],
  ["curation_status", (r) => r.meta.curation_status],
  ["missing_reasons", (r) => Object.entries(r.missing_reasons).map(([k, v]) => `${k}=${v}`).join("; ")],
  ["source_location", (r) => r.anchors.map((a) => [a.location, a.section, a.label].filter(Boolean).join(" / ")).join(" | ")],
  ["source_quote", (r) => r.anchors.map((a) => a.quote).join(" | ")],
  ["quote_verified", (r) => r.anchors.every((a) => a.quote_verified)],
];

const csvCell = (v: unknown) => {
  const s = v === null || v === undefined ? "" : String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

export async function GET(req: Request) {
  const url = new URL(req.url);
  const ids = url.searchParams.getAll("ids").flatMap((s) => s.split(",")).filter(Boolean);
  const format = url.searchParams.get("format") ?? "csv";
  const rows = rowsByIds(ids);
  if (rows.length === 0) return new Response("No matching measurements", { status: 404 });

  const pubs = new Map(corpus().map((p) => [p.publication_id, p]));
  const usedPubs = [...new Set(rows.map((r) => r.publication_id))].map((id) => pubs.get(id)!).filter(Boolean);
  // Registry outcome and endpoint for rows that are in the atlas; empty for context rows.
  const inAtlas = new Map(atlas().contrasts.map((c) => [c.id, c]));
  const derived = rows.map((r) => {
    const c = inAtlas.get(r.evidence_id);
    const pc = percentChange(r);
    return {
      evidence_id: r.evidence_id,
      atlas_outcome: c?.outcomeId ?? null,
      atlas_endpoint: c?.endpointId ?? null,
      percent_change_vs_own_control: pc ? Math.round(pc.pct * 10) / 10 : null,
      percent_change_basis: pc?.basis ?? null,
    };
  });
  const exportedAt = new Date().toISOString();
  const versions = [...new Set(rows.map((r) =>
    `${r.meta.schema_version ?? "unknown schema"} / ${r.meta.pipeline_version ?? "unknown pipeline"}`))];
  const stamp = exportedAt.slice(0, 10);
  const fixtureNote = isFixture ? "TEST FIXTURE DATA - NOT REAL EVIDENCE. " : "";

  if (format === "json") {
    const body = {
      exported_at: exportedAt,
      warning: fixtureNote || undefined,
      versions,
      limitations: LIMITATIONS,
      citations: usedPubs.map((p) => ({ publication_id: p.publication_id, doi: p.doi, citation: citation(p), license: p.license })),
      derived,
      evidence_rows: rows,
    };
    return new Response(JSON.stringify(body, null, 2), {
      headers: { "content-type": "application/json", "content-disposition": `attachment; filename="neurotwin-evidence-${stamp}.json"` },
    });
  }

  if (format === "md") {
    const lines = [
      `# NeuroTwin evidence export (${stamp})`, "",
      fixtureNote ? `**${fixtureNote.trim()}**\n` : "",
      `Measurements: ${rows.length} · Versions: ${versions.join(", ")}`, "",
      "Percent change is against each study's own control: stated by the paper, or derived from its reported values (see percent_change_basis in the CSV or JSON). Studies are not pooled.", "",
      "## Citations", "",
      ...usedPubs.map((p) => `- ${citation(p)} (license: ${p.license ?? "unknown"})`), "",
      "## Limitations", "",
      ...LIMITATIONS.map((l) => `- ${l}`), "",
    ];
    return new Response(lines.join("\n"), {
      headers: { "content-type": "text/markdown; charset=utf-8", "content-disposition": `attachment; filename="neurotwin-evidence-${stamp}.md"` },
    });
  }

  const extra = new Map(derived.map((d) => [d.evidence_id, d]));
  const header = [...COLUMNS.map(([k]) => k), "atlas_outcome", "atlas_endpoint",
                  "percent_change_vs_own_control", "percent_change_basis"];
  const body = rows.map((r) => {
    const cells = COLUMNS.map(([k, f]) => (k === "doi" ? pubs.get(r.publication_id)?.doi : f(r)));
    const d = extra.get(r.evidence_id);
    return [...cells, d?.atlas_outcome, d?.atlas_endpoint, d?.percent_change_vs_own_control,
            d?.percent_change_basis].map(csvCell).join(",");
  });
  return new Response([header.join(","), ...body].join("\n") + "\n", {
    headers: { "content-type": "text/csv; charset=utf-8", "content-disposition": `attachment; filename="neurotwin-evidence-${stamp}.csv"` },
  });
}
