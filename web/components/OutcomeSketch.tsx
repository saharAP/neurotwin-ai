"use client";

import { useState } from "react";
import { NeuronSketch, SurvivalGrid } from "./NeuronSketch";

export interface SketchItem {
  id: string;
  label: string;        // study · intervention · dose · model
  ratio: number;        // intervention / reference, from the measured percent change
  value: number | null;
  control: number | null;
  unit: string | null;
  change: string;       // e.g. "+76%"
  /** True when value and control are percentages of cells, so they can be drawn as shares. */
  shares: boolean;
}

const fmt = (x: number) => (Math.abs(x) >= 100 ? x.toFixed(0) : x.toFixed(2).replace(/\.?0+$/, ""));

/**
 * Reference vs intervention schematic for one study, scaled by its measured ratio. Never a simulation.
 * For "survival" the caller passes only items whose values are shares of cells.
 */
export function OutcomeSketch({ visual, items }: { visual: "neurogenesis" | "spines" | "branching" | "survival"; items: SketchItem[] }) {
  const [pick, setPick] = useState(items[0]?.id ?? "");
  const sel = items.find((i) => i.id === pick) ?? items[0];
  if (!sel) return null;
  const k = Math.max(0, sel.ratio);
  const base = { branches: 6, spines: visual === "spines" ? 3 : 0, newCells: visual === "neurogenesis" ? 3 : 0 };
  const after = {
    branches: visual === "branching" ? base.branches * k : base.branches,
    spines: visual === "spines" ? base.spines * k : 0,
    newCells: visual === "neurogenesis" ? base.newCells * k : 0,
  };
  const what = { neurogenesis: "number of new cells", spines: "number of spines", branching: "number of branches",
                 survival: "share of surviving cells" }[visual];
  const asShares = visual === "survival" && sel.shares && sel.value !== null && sel.control !== null;

  return (
    <div className="xp-stage">
      <label className="xp-outcome" style={{ marginTop: 0 }}>Study shown in the drawing
        <select value={sel.id} onChange={(e) => setPick(e.target.value)}>
          {items.map((i) => <option key={i.id} value={i.id}>{i.label} ({i.change})</option>)}
        </select>
      </label>
      <div className="xp-pair" style={{ marginTop: 14 }}>
        <figure>
          <figcaption>Reference</figcaption>
          {asShares ? <SurvivalGrid pct={sel.control!} color="var(--ref)" />
            : <NeuronSketch {...base} color="var(--ref)" soma="var(--soma)" />}
          <div className="xp-val">{sel.control !== null ? `${fmt(sel.control)} ${sel.unit ?? ""}` : "the study's own control"}</div>
        </figure>
        <div className="xp-divider" />
        <figure>
          <figcaption>Intervention</figcaption>
          {asShares ? <SurvivalGrid pct={sel.value!} color="var(--int)" />
            : <NeuronSketch {...after} color="var(--int)" soma="var(--soma)" />}
          <div className="xp-val">
            {sel.value !== null && sel.control !== null ? `${fmt(sel.value)} ${sel.unit ?? ""}` : sel.change}
            <span className="chip accent" style={{ marginLeft: 8 }}>×{fmt(k)}</span>
          </div>
        </figure>
      </div>
      <p className="xp-note">
        Schematic of one study. The {what} is scaled by that study&apos;s measured ratio (×{fmt(k)}), not by a model.
      </p>
    </div>
  );
}
