import Link from "next/link";
import { notFound } from "next/navigation";
import { ContrastPlot, type PlotRow } from "@/components/ContrastPlot";
import { ContrastTable } from "@/components/ContrastTable";
import { OutcomeSketch, type SketchItem } from "@/components/OutcomeSketch";
import { atlas, atlasColumns, countBy, fmtPct, type Contrast } from "@/lib/atlas";

export const dynamic = "force-dynamic";

type Search = Promise<{ intervention?: string; endpoint?: string; species?: string; level?: string }>;

const rowLabel = (c: Contrast) =>
  `${c.cite} · ${c.compound} ${c.dose.split(",")[0]}${c.region ? ` · ${c.region}` : ""}${c.time === "time not reported" ? "" : ` · ${c.time.replace(/ after .*/, "")}`}`;
/** Plot rows name the endpoint first, so two endpoints from one study never look like one. */
const plotLabel = (c: Contrast) => `${c.endpointLabel.replace(/ \(.*/, "")} · ${rowLabel(c)}`;

export default async function OutcomePage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Search }) {
  const { id } = await params;
  const sp = await searchParams;
  const data = atlas();
  const outcome = data.registry.outcomes.find((o) => o.id === id);
  if (!outcome) notFound();

  const all = data.contrasts.filter((c) => c.outcomeId === id);
  const cols = atlasColumns(data.contrasts);
  const display = new Map(cols.map((c) => [c.name, c.display]));
  const options = (key: (c: Contrast) => string) => [...new Set(all.map(key))].sort();
  const pick = (v: string | undefined, allowed: string[]) => (v && allowed.includes(v) ? v : "");
  const intervention = pick(sp.intervention, options((c) => c.intervention));
  const endpoint = pick(sp.endpoint, options((c) => c.endpointId));
  const species = pick(sp.species, options((c) => c.species));
  const level = pick(sp.level, options((c) => c.level));
  // An intervention asked for by the atlas link but with no rows here is still named in the empty state.
  const asked = sp.intervention && !intervention ? sp.intervention : "";

  const rows = asked ? [] : all
    .filter((c) => !intervention || c.intervention === intervention)
    .filter((c) => !endpoint || c.endpointId === endpoint)
    .filter((c) => !species || c.species === species)
    .filter((c) => !level || c.level === level)
    .sort((a, b) => a.endpointId.localeCompare(b.endpointId) || a.intervention.localeCompare(b.intervention)
      || a.cite.localeCompare(b.cite));

  const studies = new Set(rows.map((c) => c.pubId)).size;
  const numeric = rows.filter((c) => c.pct !== null);

  // Dots: every row with a percent change. Labels must be unique for the category axis.
  const seen = new Map<string, number>();
  const plotRows: PlotRow[] = numeric.map((c) => {
    const base = plotLabel(c);
    const k = (seen.get(base) ?? 0) + 1;
    seen.set(base, k);
    return {
      id: c.id, label: k > 1 ? `${base} (${k})` : base, group: display.get(c.intervention) ?? c.intervention, pct: c.pct!,
      hover: `${c.endpointLabel}: ${c.value}${c.control !== null ? ` vs ${c.control}` : ""} ${c.unit ?? ""}`,
    };
  });

  // Drawing: only rows with a measured ratio and no mechanism probe; survival needs shares of cells.
  const sketchItems: SketchItem[] = !outcome.visual ? [] : numeric
    .filter((c) => !c.probe)
    .map((c) => ({
      id: c.id, label: rowLabel(c), ratio: 1 + c.pct! / 100, value: c.value, control: c.control, unit: c.unit,
      change: fmtPct(c.pct!), shares: c.control !== null && /%/.test(c.unit ?? ""),
    }))
    .filter((i) => outcome.visual !== "survival" || i.shares);

  const idParam = rows.map((c) => c.id).join(",");

  return (
    <>
      <p className="small"><Link href="/">← Atlas</Link></p>
      <h1>{outcome.label}</h1>
      <p className="lead">{outcome.description} Each row is one measurement against that study&apos;s own control. Studies are shown side by side and never pooled.</p>

      <form className="filters" method="get">
        <label>Intervention
          <select name="intervention" defaultValue={intervention}>
            <option value="">All</option>
            {options((c) => c.intervention).map((v) => <option key={v} value={v}>{display.get(v) ?? v}</option>)}
          </select>
        </label>
        <label>Endpoint
          <select name="endpoint" defaultValue={endpoint}>
            <option value="">All</option>
            {outcome.endpoints.filter((e) => all.some((c) => c.endpointId === e.id))
              .map((e) => <option key={e.id} value={e.id}>{e.label}</option>)}
          </select>
        </label>
        <label>Species
          <select name="species" defaultValue={species}>
            <option value="">All</option>
            {options((c) => c.species).map((v) => <option key={v}>{v}</option>)}
          </select>
        </label>
        <label>Evidence level
          <select name="level" defaultValue={level}>
            <option value="">All</option>
            {options((c) => c.level).map((v) => <option key={v}>{v}</option>)}
          </select>
        </label>
        <button type="submit">Apply</button>
        {(intervention || endpoint || species || level || asked) && <Link className="btn" href={`/outcomes/${id}`}>Clear</Link>}
      </form>

      {asked && (
        <p className="small">No measurements of this outcome under <strong>{display.get(asked) ?? asked}</strong> in the papers read so far.</p>
      )}

      <div className="stats">
        <div className="stat"><div className="stat-l">Measurements</div><div className="stat-v">{rows.length}</div></div>
        <div className="stat"><div className="stat-l">Studies</div><div className="stat-v">{studies}</div></div>
        <div className="stat"><div className="stat-l">With a number in the text</div><div className="stat-v">{numeric.length}</div></div>
        <div className="stat"><div className="stat-l">Evidence levels</div><div className="stat-v small-v">{countBy(rows, (c) => c.level).map(([l, n]) => `${l} (${n})`).join(", ") || "—"}</div></div>
      </div>

      <h2>Change against each study&apos;s own control</h2>
      {plotRows.length > 0 ? (
        <div className="card">
          <p className="small muted" style={{ marginTop: 0 }}>
            One dot per measurement. Percent change is stated by the paper or derived from its reported values;
            the table below says which. Different endpoints, species and doses share this axis only for
            reading side by side: there is no pooled estimate and no fitted line. Click a dot to open its source quote.
          </p>
          <ContrastPlot rows={plotRows} />
          {rows.length > numeric.length && (
            <p className="small muted" style={{ marginBottom: 0 }}>
              {rows.length - numeric.length} more measurement{rows.length - numeric.length === 1 ? " is" : "s are"} not
              plotted because the paper gives the direction but no number in its text (usually the number is only in a figure).
            </p>
          )}
        </div>
      ) : (
        <div className="card empty-state">
          {rows.length === 0 ? "Nothing to plot for this selection."
            : "These papers give the direction of change but no number in their text (usually only in a figure), so nothing can be plotted."}
        </div>
      )}

      {sketchItems.length > 0 && outcome.visual && (
        <>
          <h2>What one study measured</h2>
          <OutcomeSketch visual={outcome.visual} items={sketchItems} />
        </>
      )}

      <h2>Measurements</h2>
      <ContrastTable rows={rows} />

      {rows.length > 0 && (
        <div className="actions">
          <a className="btn primary" href={`/api/export?format=csv&ids=${idParam}`}>Download CSV</a>
          <a className="btn" href={`/api/export?format=json&ids=${idParam}`}>Download JSON</a>
          <a className="btn" href={`/api/export?format=md&ids=${idParam}`}>Citations and limitations (.md)</a>
        </div>
      )}
      <p className="small muted" style={{ marginTop: 16 }}>
        Model state (healthy or under an insult such as stress or hypoxia) is not a separate field yet; read it in the
        Model column and the source quote.
      </p>
    </>
  );
}
