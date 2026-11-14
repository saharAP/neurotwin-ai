import Link from "next/link";
import { notFound } from "next/navigation";
import { ContrastTable } from "@/components/ContrastTable";
import { atlas } from "@/lib/atlas";
import { publication, rowsFor, screening } from "@/lib/data";
import { citation, doseText, label, timeText, valueText } from "@/lib/format";
import { evidenceLevel } from "@/lib/levels";

export const dynamic = "force-dynamic";

export default async function StudyPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const p = publication(id);
  if (!p) notFound();
  const rows = rowsFor(id);
  const data = atlas();
  const mine = data.contrasts.filter((c) => c.pubId === id);
  const atlasIds = new Set(mine.map((c) => c.id));
  const context = rows.filter((r) => !atlasIds.has(r.evidence_id));
  const screen = screening().find((s) => s.publication_id === id);
  const ext = p.extended;
  const designs = [...new Set(rows.map((r) => label(r.experiment.design)))];
  const levels = [...new Set(rows.map((r) => evidenceLevel(r.experiment.design, r.experiment.species)))];
  const species = [...new Set(rows.map((r) => r.experiment.species))];
  const status = !screen ? "Not read yet"
    : !screen.reports_measured_outcomes ? `Read: no measured outcomes in scope. ${screen.reason}`
    : `Read: ${rows.length} measurement${rows.length === 1 ? "" : "s"} extracted`;
  const idParam = rows.map((r) => r.evidence_id).join(",");

  return (
    <>
      <p className="small"><Link href="/studies">← Studies</Link></p>
      <h1>{p.title}</h1>
      <p className="muted">{citation(p)}</p>
      <div className="chips">
        <span className="chip accent">{label(p.publication_type)}</span>
        <span className="chip">{label(p.peer_review_status)}</span>
        {ext.corpus?.substances.map((s) => <span key={s} className="chip">{s}</span>)}
        {levels.map((l) => <span key={l} className="chip">{l}</span>)}
        {p.is_retracted && <span className="chip bad">retracted</span>}
        {(ext.corrections?.length ?? 0) > 0 && <span className="chip warn">has corrections</span>}
      </div>

      <div className="grid-2" style={{ marginTop: 16 }}>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Study</h3>
          <dl className="kv">
            <dt>Status</dt><dd>{status}</dd>
            <dt>Design</dt><dd>{designs.join(", ") || "—"}</dd>
            <dt>Species</dt><dd>{species.join(", ") || "—"}</dd>
            <dt>In the atlas</dt><dd>{mine.length} measurement{mine.length === 1 ? "" : "s"}</dd>
            <dt>Context only</dt><dd>{context.length} measurement{context.length === 1 ? "" : "s"}</dd>
          </dl>
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Source</h3>
          <dl className="kv">
            <dt>DOI</dt><dd>{p.doi ? <a href={`https://doi.org/${p.doi}`} target="_blank" rel="noreferrer">{p.doi}</a> : "—"}</dd>
            <dt>Full text</dt><dd>{p.pmcid ? <a href={`https://europepmc.org/article/PMC/${p.pmcid}`} target="_blank" rel="noreferrer">{p.pmcid} (Europe PMC)</a> : label(p.full_text_access)}</dd>
            <dt>License</dt><dd>{p.license ?? "—"}</dd>
            <dt>Funding</dt><dd>{ext.funding?.length ? ext.funding.map((f) => f.agency ?? f.statement).filter(Boolean).slice(0, 4).join("; ") : "not reported"}</dd>
            <dt>Conflicts</dt><dd className="small">{ext.conflicts_of_interest ?? "no statement found"}</dd>
          </dl>
        </div>
      </div>

      {data.registry.outcomes.map((o) => {
        const cs = mine.filter((c) => c.outcomeId === o.id);
        if (cs.length === 0) return null;
        return (
          <section key={o.id}>
            <h2><Link href={`/outcomes/${o.id}`}>{o.label}</Link></h2>
            <ContrastTable rows={cs} showStudy={false} />
          </section>
        );
      })}
      {screen?.reports_measured_outcomes && mine.length === 0 && (
        <p className="small muted" style={{ marginTop: 16 }}>None of this paper&apos;s measurements are on the atlas&apos;s five neuron outcomes.</p>
      )}

      {context.length > 0 && (
        <>
          <h2>Context measurements</h2>
          <p className="small muted">Outside the five neuron outcomes (behavior, clinical scales, brain imaging, molecular markers). Kept for reference; not shown in the atlas.</p>
          <div className="table-scroll card" style={{ padding: 0 }}>
            <table className="data">
              <thead><tr><th>Endpoint</th><th>Arm · dose</th><th>Time</th><th>Value</th><th>Direction</th></tr></thead>
              <tbody>
                {context.map((r) => (
                  <tr key={r.evidence_id}>
                    <td>
                      {r.measurement.endpoint_original}
                      <div className="small muted">{label(r.measurement.scale_level)} · {evidenceLevel(r.experiment.design, r.experiment.species)}</div>
                      <details className="src">
                        <summary>source quote</summary>
                        <blockquote className="quote">“{r.anchors[0]?.quote}”</blockquote>
                      </details>
                    </td>
                    <td>{r.arm.label}<div className="small muted">{doseText(r)}</div></td>
                    <td className="small">{timeText(r)}</td>
                    <td className="small mono">{valueText(r)}</td>
                    <td>{label(r.measurement.effect_direction)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {rows.length > 0 && (
        <div className="actions">
          <a className="btn primary" href={`/api/export?format=csv&ids=${idParam}`}>Download CSV</a>
          <a className="btn" href={`/api/export?format=json&ids=${idParam}`}>Download JSON</a>
          <a className="btn" href={`/api/export?format=md&ids=${idParam}`}>Citations and limitations (.md)</a>
        </div>
      )}

      <p className="small muted" style={{ marginTop: 16 }}>
        Record {p.publication_id} · schema {p.meta.schema_version} · {p.meta.pipeline_version}
      </p>
    </>
  );
}
