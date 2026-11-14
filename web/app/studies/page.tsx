import Link from "next/link";
import { atlas, atlasColumns } from "@/lib/atlas";
import { corpus, evidenceRows, screening } from "@/lib/data";
import { shortCite } from "@/lib/format";

export const dynamic = "force-dynamic";

type Search = Promise<{ intervention?: string; status?: string }>;

const STATUSES = { atlas: "In the atlas", context: "Context only", none: "No measured outcomes", unread: "Not read yet" } as const;
type Status = keyof typeof STATUSES;

export default async function StudiesPage({ searchParams }: { searchParams: Search }) {
  const sp = await searchParams;
  const data = atlas();
  const cols = atlasColumns(data.contrasts);
  const all = corpus();
  const screened = new Map(screening().map((s) => [s.publication_id, s]));
  const total = new Map<string, number>();
  for (const r of evidenceRows()) total.set(r.publication_id, (total.get(r.publication_id) ?? 0) + 1);
  const inAtlas = new Map<string, number>();
  for (const c of data.contrasts) inAtlas.set(c.pubId, (inAtlas.get(c.pubId) ?? 0) + 1);
  const statusOf = (id: string): Status =>
    inAtlas.has(id) ? "atlas" : total.has(id) ? "context" : screened.has(id) ? "none" : "unread";

  const intervention = cols.some((c) => c.name === sp.intervention) ? sp.intervention! : "";
  const status = sp.status && sp.status in STATUSES ? (sp.status as Status) : "";
  const order: Status[] = ["atlas", "context", "unread", "none"];
  const pubs = all
    .filter((p) => !intervention || p.extended.corpus?.substances.includes(intervention))
    .filter((p) => !status || statusOf(p.publication_id) === status)
    .sort((a, b) => order.indexOf(statusOf(a.publication_id)) - order.indexOf(statusOf(b.publication_id))
      || (b.year ?? 0) - (a.year ?? 0));

  return (
    <>
      <h1>Studies</h1>
      <p className="lead">Every paper in the corpus, and whether it has been read. Open a study for its measurements and their source quotes.</p>

      <form className="filters" method="get">
        <label>Intervention
          <select name="intervention" defaultValue={intervention}>
            <option value="">All</option>
            {cols.filter((c) => all.some((p) => p.extended.corpus?.substances.includes(c.name)))
              .map((c) => <option key={c.name} value={c.name}>{c.display}</option>)}
          </select>
        </label>
        <label>Status
          <select name="status" defaultValue={status}>
            <option value="">All</option>
            {Object.entries(STATUSES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        <button type="submit">Apply</button>
        {(intervention || status) && <Link className="btn" href="/studies">Clear</Link>}
      </form>

      <p className="small muted">{pubs.length} of {all.length} papers</p>
      {pubs.length === 0 ? (
        <div className="card empty-state">No papers match these filters.</div>
      ) : (
        <div className="table-scroll card" style={{ padding: 0 }}>
          <table className="data">
            <thead><tr><th>Paper</th><th>Interventions</th><th>Status</th><th>Atlas</th><th>Context</th></tr></thead>
            <tbody>
              {pubs.map((p) => {
                const s = statusOf(p.publication_id);
                const a = inAtlas.get(p.publication_id) ?? 0;
                return (
                  <tr key={p.publication_id}>
                    <td>
                      <Link href={`/studies/${p.publication_id}`}>{p.title}</Link>
                      <div className="small muted">{shortCite(p)} · {p.journal}</div>
                    </td>
                    <td className="small">{p.extended.corpus?.substances.join(", ")}</td>
                    <td><span className={`chip ${s === "atlas" ? "ok" : s === "unread" ? "warn" : ""}`}>{STATUSES[s]}</span></td>
                    <td>{a || "—"}</td>
                    <td>{(total.get(p.publication_id) ?? 0) - a || "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
