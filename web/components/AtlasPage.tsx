import Link from "next/link";
import { atlas, atlasColumns, countBy, type Column, type Contrast, type Outcome } from "@/lib/atlas";
import { corpus, screening } from "@/lib/data";
import { label } from "@/lib/format";

function Cell({ outcome, col, rows }: { outcome: Outcome; col: Column; rows: Contrast[] }) {
  if (rows.length === 0) {
    const why = col.papers === 0 ? "no papers" : col.unread === col.papers ? "not read yet" : "gap";
    return <div className="cell empty"><div className="small">{why}</div></div>;
  }
  const studies = new Set(rows.map((r) => r.pubId)).size;
  // A probe arm tests mechanism (e.g. a receptor blocker): its direction is not the intervention's effect.
  const plain = rows.filter((r) => !r.probe);
  const probes = rows.length - plain.length;
  const withNumbers = plain.filter((r) => r.pct !== null).length;
  return (
    <Link className="cell" href={`/outcomes/${outcome.id}?intervention=${encodeURIComponent(col.name)}`}>
      <div className="count">{studies}</div>
      <div className="small">stud{studies === 1 ? "y" : "ies"} · {rows.length} measurement{rows.length === 1 ? "" : "s"}</div>
      <div className="chips">
        {countBy(plain, (r) => r.direction).map(([d, n]) => <span key={d} className="chip">{label(d)}: {n}</span>)}
        {countBy(rows, (r) => r.level).map(([l, n]) => <span key={l} className="chip accent">{l}: {n}</span>)}
        {withNumbers > 0 && <span className="chip ok">with numbers: {withNumbers}</span>}
        {probes > 0 && <span className="chip warn">mechanism probes: {probes}</span>}
      </div>
    </Link>
  );
}

export function AtlasPage() {
  const data = atlas();
  const cols = atlasColumns(data.contrasts);
  const pubs = corpus();
  const read = screening().length;
  const studies = new Set(data.contrasts.map((c) => c.pubId)).size;
  const markerRows = data.contextMarkers.reduce((n, m) => n + m.rows, 0);

  return (
    <>
      <h1>Neuron outcome atlas</h1>
      <p className="lead">
        How neurons change under different interventions, one outcome per row. Each cell counts the
        studies that measured that outcome under that intervention. Open a cell to see every
        measurement against its own control, with the source quote. Nothing is pooled or scored.
      </p>
      <p className="small muted">
        {data.contrasts.length} measurements from {studies} studies are in the atlas ·{" "}
        {read} of {pubs.length} papers read · preclinical evidence only (cells, animals, human-derived cells) ·{" "}
        <Link href="/about">how this was built</Link>
      </p>
      {data.registry.status !== "reviewed" && (
        <p className="small"><span className="chip warn">draft</span> The list of outcomes and endpoints is a draft and has not been reviewed by a neuroscientist.</p>
      )}

      <div className="map-scroll">
        <table className="map atlas">
          <thead>
            <tr>
              <th style={{ width: 170 }}></th>
              {cols.map((c) => (
                <th key={c.name}>
                  {c.display}
                  <div className="small muted" style={{ fontWeight: 400 }}>
                    {c.papers} paper{c.papers === 1 ? "" : "s"}{c.unread > 0 ? ` · ${c.unread} not read` : ""}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.registry.outcomes.map((o) => (
              <tr key={o.id}>
                <th scope="row">
                  <Link href={`/outcomes/${o.id}`}>{o.label}</Link>
                  <div className="small muted" style={{ fontWeight: 400 }}>{o.description}</div>
                </th>
                {cols.map((c) => (
                  <td key={c.name}>
                    <Cell outcome={o} col={c}
                          rows={data.contrasts.filter((r) => r.outcomeId === o.id && r.intervention === c.name)} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="small muted" style={{ marginTop: 12 }}>
        &quot;Gap&quot; means the papers read so far report no measurement there. It is a gap in this corpus,
        not evidence of no effect. Direction of change is not benefit or harm.
      </p>

      <h2>Kept as context, not in the atlas</h2>
      <div className="card">
        <dl className="kv">
          {data.contextMarkers.map((m) => (
            <div key={m.id} style={{ display: "contents" }}>
              <dt>{m.label}</dt><dd>{m.rows} measurement{m.rows === 1 ? "" : "s"} from {m.studies} stud{m.studies === 1 ? "y" : "ies"}</dd>
            </div>
          ))}
          <dt>Other endpoints</dt>
          <dd>{data.otherRows} measurements (behavior, clinical scales, brain imaging, receptors). They stay on each <Link href="/studies">study page</Link>.</dd>
        </dl>
        <p className="small muted" style={{ marginBottom: 0 }}>
          {markerRows + data.otherRows} of {data.totalRows} extracted measurements are outside the five outcomes.
        </p>
      </div>
    </>
  );
}
