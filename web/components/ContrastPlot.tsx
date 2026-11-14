"use client";

import { useEffect, useRef } from "react";

export interface PlotRow {
  id: string;
  label: string;   // one line per study contrast
  group: string;   // intervention, used for colour and legend
  pct: number;     // percent change against the study's own control
  hover: string;   // original numbers
}

/**
 * One dot per study contrast on a shared percent-change axis. No pooled estimate, no fitted
 * line, no error bars: most papers report uncertainty for one group only, so an interval on
 * the change cannot be computed honestly. Clicking a dot opens that row's source quote.
 */
export function ContrastPlot({ rows }: { rows: PlotRow[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    const el = ref.current;
    (async () => {
      const Plotly = (await import("plotly.js-dist-min")).default;
      if (cancelled || !el) return;
      const css = getComputedStyle(document.documentElement);
      const text = css.getPropertyValue("--text").trim();
      const grid = css.getPropertyValue("--border").trim();
      const order = [...rows].reverse(); // first row at the top
      // On a narrow screen the row labels would take the whole width as axis ticks,
      // so each label is written above its own dot instead.
      const narrow = el.clientWidth < 620;
      const clip = (s: string) => (s.length > 52 ? `${s.slice(0, 51)}…` : s);
      const traces = [...new Set(rows.map((r) => r.group))].map((g) => {
        const rs = order.filter((r) => r.group === g);
        return {
          type: "scatter", mode: "markers", name: g,
          x: rs.map((r) => r.pct), y: rs.map((r) => r.label),
          customdata: rs.map((r) => r.id), text: rs.map((r) => r.hover),
          hovertemplate: "%{y}<br>%{x:+.1f}% vs own control<br>%{text}<extra></extra>",
          marker: { size: 11 },
        };
      });
      await Plotly.newPlot(el, traces, {
        height: narrow ? 120 + 46 * rows.length : 130 + 30 * rows.length,
        margin: { t: narrow ? 24 : 10, r: 16, b: 56, l: 10 },
        annotations: narrow ? order.map((r) => ({
          xref: "paper", x: 0, xanchor: "left", yref: "y", y: r.label, yshift: 14,
          text: clip(r.label), showarrow: false, font: { size: 11, color: text }, align: "left",
        })) : [],
        paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: text, size: 12 },
        xaxis: { title: { text: narrow ? "% change vs own control" : "% change against the study's own control" },
                 gridcolor: grid,
                 zeroline: true, zerolinecolor: text, zerolinewidth: 1, ticksuffix: "%",
                 rangemode: "tozero" },
        yaxis: { type: "category", categoryorder: "array", categoryarray: order.map((r) => r.label),
                 automargin: true, gridcolor: grid, showticklabels: !narrow },
        legend: { orientation: "h", y: -0.2 - 2 / Math.max(4, rows.length) },
        showlegend: traces.length > 1,
      }, { displaylogo: false, responsive: true, displayModeBar: false });
      (el as unknown as { on: (ev: string, cb: (e: { points: { customdata: string }[] }) => void) => void })
        .on("plotly_click", (e) => {
          const id = e.points?.[0]?.customdata;
          const row = id ? document.getElementById(`row-${id}`) : null;
          const det = id ? document.getElementById(`src-${id}`) as HTMLDetailsElement | null : null;
          document.querySelectorAll("tr.hit").forEach((x) => x.classList.remove("hit"));
          if (det) det.open = true;
          if (row) { row.classList.add("hit"); row.scrollIntoView({ behavior: "smooth", block: "center" }); }
        });
    })();
    return () => {
      cancelled = true;
      if (el) import("plotly.js-dist-min").then((m) => m.default.purge(el));
    };
  }, [rows]);

  return <div ref={ref} className="plot-h" role="img" aria-label="Percent change against each study's own control, one dot per study contrast" />;
}
