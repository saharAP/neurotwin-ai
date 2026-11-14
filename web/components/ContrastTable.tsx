import Link from "next/link";
import { fmtPct, type Contrast } from "@/lib/atlas";
import { label } from "@/lib/format";

const BASIS: Record<string, string> = {
  reported: "stated in the paper",
  from_fold: "derived from the reported fold change",
  from_values: "derived from the two reported values",
};

export function Change({ c }: { c: Contrast }) {
  if (c.pct === null)
    return <span className="small">{label(c.direction)}<div className="muted">size not reported in text</div></span>;
  return (
    <span>
      <span className={`change ${c.pct > 0 ? "up" : c.pct < 0 ? "down" : ""}`}>{fmtPct(c.pct)}</span>
      <div className="small muted">{BASIS[c.pctBasis ?? ""]}</div>
    </span>
  );
}

/** One row per study contrast, each with its source quote. Used on the outcome and study pages. */
export function ContrastTable({ rows, showStudy = true, showEndpoint = true }:
  { rows: Contrast[]; showStudy?: boolean; showEndpoint?: boolean }) {
  if (rows.length === 0)
    return <div className="card empty-state">No measurements match. That is a gap in this corpus, not evidence of no effect.</div>;
  return (
    <div className="table-scroll card" style={{ padding: 0 }}>
      <table className="data">
        <thead>
          <tr>
            {showStudy && <th>Study</th>}
            {showEndpoint && <th>Endpoint</th>}
            <th>Intervention · dose</th>
            <th>Model</th>
            <th>Time</th>
            <th>Reported values</th>
            <th>Change vs own control</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id} id={`row-${c.id}`}>
              {showStudy && (
                <td>
                  <Link href={`/studies/${c.pubId}`}>{c.cite}</Link>
                  <div className="small muted">{c.level}</div>
                </td>
              )}
              {showEndpoint && (
                <td>
                  {c.endpointLabel}
                  <div className="small muted">{c.endpointOriginal}{c.assay ? ` · ${c.assay}` : ""}</div>
                </td>
              )}
              <td>
                {c.compound}{c.probe && <> <span className="chip warn">+ {c.probe}</span></>}
                <div className="small muted">{c.dose} · vs {c.comparator}</div>
              </td>
              <td>
                {c.species}
                <div className="small muted">{c.model}</div>
              </td>
              <td className="small">{c.time}</td>
              <td className="small">
                {c.value !== null ? (
                  <span className="mono">
                    {c.value}{c.control !== null ? ` vs ${c.control}` : ""} {c.unit ?? ""}
                    {c.uncertainty ? ` (${c.uncertainty})` : ""}
                  </span>
                ) : <span className="muted">no number in text</span>}
                <div className="muted">
                  {c.n !== null ? `n = ${c.n}${c.nUnit === "other" ? "" : ` ${c.nUnit.replace(/_/g, " ")}s`}` : "n not reported"}{c.p ? ` · p ${/^[<>=]/.test(c.p) ? c.p : `= ${c.p}`}` : ""}
                </div>
              </td>
              <td>
                <Change c={c} />
                <details className="src" id={`src-${c.id}`}>
                  <summary>source quote</summary>
                  <blockquote className="quote" style={{ minWidth: 220 }}>“{c.quote}”</blockquote>
                  <div className="chips" style={{ marginTop: 0 }}>
                    <span className={`chip ${c.verified ? "ok" : "bad"}`}>{c.verified ? "quote found in paper" : "quote not verified"}</span>
                    {c.quoteWhere && <span className="chip">{c.quoteWhere}</span>}
                    <span className="chip warn">{label(c.agreement)}</span>
                  </div>
                </details>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
