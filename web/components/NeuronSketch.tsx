// Schematic neuron drawings whose features are scaled by measured ratios.
// They are illustrations of a reported number, never a simulation.

type Pt = [number, number];
const r1 = (x: number) => Math.round(x * 10) / 10; // fixed precision: identical on server and client

function rng(seed: number) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Branch segments of an apical tree. Same seed -> same base shape, so extra branches add on top. */
function tree(nPrimary: number, seed = 7): [Pt, Pt][] {
  const r = rng(seed);
  const segs: [Pt, Pt][] = [];
  const top: Pt = [150, 60];
  segs.push([[150, 188], top]);
  for (let i = 0; i < nPrimary; i++) {
    const side = i % 2 === 0 ? -1 : 1;
    const y = 172 - (i / Math.max(1, nPrimary - 1)) * 92 + (r() - 0.5) * 8;
    const len = 45 + r() * 35;
    const ang = (-35 - r() * 30) * (Math.PI / 180);
    const start: Pt = [150, y];
    const end: Pt = [150 + side * Math.cos(ang) * len, y + Math.sin(ang) * len];
    segs.push([start, end]);
    // one or two secondary branches near the tip
    const nSec = 1 + (r() > 0.5 ? 1 : 0);
    for (let k = 0; k < nSec; k++) {
      const t = 0.55 + r() * 0.35;
      const s: Pt = [start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t];
      const a2 = ang + side * (k === 0 ? 0.6 : -0.5) * (side > 0 ? -1 : 1);
      const l2 = 18 + r() * 22;
      segs.push([s, [s[0] + side * Math.cos(a2) * l2, s[1] + Math.sin(a2) * l2 - 6]]);
    }
  }
  return segs.map(([a, b]) => [[r1(a[0]), r1(Math.max(8, a[1]))], [r1(b[0]), r1(Math.max(8, b[1]))]] as [Pt, Pt]);
}

export interface SketchProps {
  branches?: number;   // number of primary dendrites
  spines?: number;     // spine ticks per segment
  newCells?: number;   // small newborn cells near the soma
  color: string;
  soma: string;
}

export function NeuronSketch({ branches = 6, spines = 0, newCells = 0, color, soma }: SketchProps) {
  const segs = tree(Math.max(2, Math.min(16, Math.round(branches))));
  const ticks: [Pt, Pt][] = [];
  if (spines > 0) {
    segs.slice(1).forEach(([a, b]) => {
      const n = Math.max(0, Math.round(spines));
      for (let i = 1; i <= n; i++) {
        const t = i / (n + 1);
        const p: Pt = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
        const dx = b[0] - a[0], dy = b[1] - a[1];
        const L = Math.hypot(dx, dy) || 1;
        const nx = (-dy / L) * 6, ny = (dx / L) * 6;
        ticks.push([[r1(p[0]), r1(p[1])], [r1(p[0] + (i % 2 ? nx : -nx)), r1(p[1] + (i % 2 ? ny : -ny))]]);
      }
    });
  }
  const cells = Array.from({ length: Math.min(10, Math.round(newCells)) }, (_, i) => {
    const ang = (i / 10) * Math.PI * 2;
    return [r1(150 + Math.cos(ang) * 48 + (i % 2) * 6), r1(248 + Math.sin(ang) * 14)] as Pt;
  });
  return (
    <svg viewBox="0 0 300 300" className="neuron" aria-hidden="true">
      {segs.map(([a, b], i) => (
        <line key={i} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={color} strokeWidth={i === 0 ? 5 : 3.5} strokeLinecap="round" />
      ))}
      {ticks.map(([a, b], i) => (
        <line key={`t${i}`} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={color} strokeWidth={2} strokeLinecap="round" />
      ))}
      <line x1={140} y1={205} x2={112} y2={285} stroke={color} strokeWidth={3.5} strokeLinecap="round" />
      <line x1={160} y1={205} x2={188} y2={285} stroke={color} strokeWidth={3.5} strokeLinecap="round" />
      {cells.map(([x, y], i) => <circle key={`c${i}`} cx={x} cy={y} r={7} fill={color} opacity={0.75} />)}
      <circle cx={150} cy={195} r={22} fill={color} />
      <circle cx={150} cy={195} r={8} fill={soma} />
    </svg>
  );
}

/** Ten cells, a reported percentage of them alive (filled), for survival or viability outcomes. */
export function SurvivalGrid({ pct, color }: { pct: number; color: string }) {
  const alive = Math.round(Math.max(0, Math.min(100, pct)) / 10);
  return (
    <svg viewBox="0 0 300 300" className="neuron" aria-hidden="true">
      {Array.from({ length: 10 }, (_, i) => {
        const x = 45 + (i % 5) * 52, y = 110 + Math.floor(i / 5) * 80;
        const on = i < alive;
        return (
          <g key={i} opacity={on ? 1 : 0.25}>
            <line x1={x} y1={y} x2={x} y2={y - 34} stroke={color} strokeWidth={3} strokeLinecap="round" />
            <line x1={x} y1={y - 18} x2={x - 12} y2={y - 30} stroke={color} strokeWidth={2.5} strokeLinecap="round" />
            <line x1={x} y1={y - 22} x2={x + 12} y2={y - 34} stroke={color} strokeWidth={2.5} strokeLinecap="round" />
            <circle cx={x} cy={y} r={10} fill={on ? color : "none"} stroke={color} strokeWidth={2} />
          </g>
        );
      })}
    </svg>
  );
}
