import { Fragment } from "react";
import { atlas } from "@/lib/atlas";
import { corpus, evidenceRows, interventions, pipelineStats, screening } from "@/lib/data";
import { label, LIMITATIONS } from "@/lib/format";

export const dynamic = "force-dynamic";

export default function About() {
  const s = pipelineStats();
  const pubs = corpus();
  const rows = evidenceRows();
  const split = pubs.reduce<Record<string, number>>((acc, p) => {
    const k = p.extended.corpus?.split ?? "?";
    acc[k] = (acc[k] ?? 0) + 1;
    return acc;
  }, {});

  // Extraction status, counted from the data so it never drifts from the pipeline output.
  const corpusIds = new Set(pubs.map((p) => p.publication_id));
  const screened = screening().filter((x) => corpusIds.has(x.publication_id));
  const withRows = new Set(rows.map((r) => r.publication_id)).size;
  const noOutcomes = screened.filter((x) => !x.reports_measured_outcomes).length;
  const count = (key: (r: (typeof rows)[number]) => string) =>
    Object.entries(rows.reduce<Record<string, number>>((acc, r) => {
      acc[key(r)] = (acc[key(r)] ?? 0) + 1;
      return acc;
    }, {}));
  const agreement = count((r) => r.agreement);
  const versions = count((r) => r.meta.schema_version);
  const doubleChecked = rows.filter((r) => r.agreement === "ai_consistent" || r.agreement === "ai_disputed").length;
  const reviewed = rows.filter((r) => r.meta.curation_status === "verified").length;
  const a = atlas();
  const atlasNumeric = a.contrasts.filter((c) => c.pct !== null).length;

  return (
    <>
      <h1>About the data</h1>
      <p className="lead">
        NeuroTwin studies how neurons change under different substances and environmental settings: neurogenesis, spinogenesis, dendritogenesis, neuroplasticity and neurodegenerative features.
        It can cover any substance discussed in the literature, and non-substance interventions such as
        sleep, exercise or an environmental setting. The corpus loaded now covers {interventions().map((i) => i.display).join(", ")};
        that list is a configuration file, not the project&apos;s scope.
      </p>
      <p className="lead">
        How the v0 corpus was built: OPEN Foundation is used only to find reference papers; all data and
        citations come from the papers themselves, via Europe PMC.
      </p>

      <h2>Selection funnel</h2>
      <div className="card">
        <dl className="kv">
          <dt>OPEN posts scanned</dt><dd>{s.discovered} ({interventions().map((i) => i.name).join(", ")})</dd>
          <dt>PubMed / Europe PMC search hits</dt><dd>{s.searched} (open-access primary studies; substance in title, neuroplasticity term in title or abstract)</dd>
          <dt>Papers resolved in Europe PMC</dt><dd>{s.resolved}</dd>
          <dt>References not resolved</dt><dd>{s.unresolved}</dd>
          {Object.entries(s.excluded).map(([code, n]) => (
            <Fragment key={code}><dt>Excluded: {label(code)}</dt><dd>{n}</dd></Fragment>
          ))}
          <dt>Corpus</dt><dd>{pubs.length} papers ({Object.entries(split).map(([k, n]) => `${n} ${k}`).join(", ")})</dd>
          <dt>Measurements extracted</dt><dd>{rows.length}</dd>
        </dl>
      </div>

      <h2>Atlas coverage</h2>
      <div className="card">
        <dl className="kv">
          <dt>Outcomes</dt><dd>{a.registry.outcomes.map((o) => o.label).join(", ")}</dd>
          <dt>Endpoint registry</dt><dd>{a.registry.status === "reviewed" ? "Reviewed" : "Draft: not reviewed by a neuroscientist"}</dd>
          <dt>Measurements in the atlas</dt><dd>{a.contrasts.length} of {a.totalRows}, from {new Set(a.contrasts.map((c) => c.pubId)).size} studies</dd>
          <dt>With a percent change</dt><dd>{atlasNumeric} of {a.contrasts.length} (stated by the paper or derived from its reported values; the rest give a direction only)</dd>
          <dt>Kept as context</dt><dd>{a.totalRows - a.contrasts.length} measurements outside the five outcomes, shown on each study page</dd>
        </dl>
      </div>

      <h2>Extraction status</h2>
      <div className="card">
        <dl className="kv">
          <dt>Papers read</dt><dd>{screened.length} of {pubs.length}</dd>
          <dt>With measurements</dt><dd>{withRows}</dd>
          <dt>Read, no measured outcomes in scope</dt><dd>{noOutcomes}</dd>
          <dt>Not read yet</dt><dd>{pubs.length - screened.length}</dd>
          <dt>Agreement status</dt><dd>{agreement.map(([k, n]) => `${n} ${label(k)}`).join(", ") || "—"}</dd>
          <dt>Second AI pass</dt><dd>{doubleChecked === 0 ? "Not run yet: every value comes from one extraction pass" : `${doubleChecked} of ${rows.length} measurements checked by two passes`}</dd>
          <dt>Expert review</dt><dd>{reviewed === 0 ? "None: no measurement has been verified by a reviewer" : `${reviewed} of ${rows.length} measurements verified`}</dd>
          <dt>Schema version</dt><dd>{versions.map(([k, n]) => `${k} (${n})`).join(", ") || "—"}</dd>
        </dl>
        <p className="small muted" style={{ marginBottom: 0 }}>
          Every measurement carries a source quote that code found in the paper text. Time units use one
          spelling per unit; values and units are otherwise as the authors reported them.
        </p>
      </div>

      <h2>Limitations</h2>
      <ul>{LIMITATIONS.map((l) => <li key={l}>{l}</li>)}</ul>
    </>
  );
}
