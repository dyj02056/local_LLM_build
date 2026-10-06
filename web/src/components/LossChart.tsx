import { useRef, useState } from "react";
import lossV1 from "../data/loss.json";
import lossV2 from "../data/loss_v2.json";
import lossV3 from "../data/loss_v3.json";

const W = 640;
const H = 240;
const PAD = { l: 44, r: 16, t: 14, b: 30 };
const WINDOW = 10;
const MAX_Y = 0.45;

type Run = { id: string; label: string; points: [number, number][]; smooth: number[]; dash?: string };

function smoothOf(points: [number, number][]) {
  return points.map((_, i) => {
    const s = points.slice(Math.max(0, i - WINDOW + 1), i + 1);
    return s.reduce((a, [, v]) => a + v, 0) / s.length;
  });
}

// 실행은 색이 아니라 선 모양으로 구분한다 (실선 = v1, 긴 점선 = v2, 짧은 점선 = v3)
const RUNS: Run[] = [
  { id: "v1", label: "v1 Spider", points: lossV1 as [number, number][], smooth: [] },
  { id: "v2", label: "v2 Spider+한국어", points: lossV2 as [number, number][], smooth: [], dash: "5 4" },
  { id: "v3", label: "v3 JOIN 균형", points: lossV3 as [number, number][], smooth: [], dash: "1.5 3" },
].map((r) => ({ ...r, smooth: smoothOf(r.points) }));

const maxStep = Math.max(...RUNS.map((r) => r.points[r.points.length - 1][0]));
const x = (s: number) => PAD.l + (s / maxStep) * (W - PAD.l - PAD.r);
const y = (v: number) => PAD.t + (1 - v / MAX_Y) * (H - PAD.t - PAD.b);
const path = (r: Run, vals: number[]) => r.points.map(([s], i) => `${i ? "L" : "M"}${x(s)},${y(vals[i])}`).join("");

/** 가장 가까운 기록 지점 (그 실행의 범위를 벗어나면 null) */
function nearest(r: Run, step: number) {
  const last = r.points[r.points.length - 1][0];
  if (step > last + 10) return null;
  let best = 0;
  for (let i = 1; i < r.points.length; i++) if (Math.abs(r.points[i][0] - step) < Math.abs(r.points[best][0] - step)) best = i;
  return best;
}

export function LossChart() {
  const ref = useRef<SVGSVGElement>(null);
  const [step, setStep] = useState<number | null>(null);

  function onMove(e: React.PointerEvent<SVGSVGElement>) {
    const box = ref.current!.getBoundingClientRect();
    const sx = ((e.clientX - box.left) / box.width) * W;
    const s = ((sx - PAD.l) / (W - PAD.l - PAD.r)) * maxStep;
    setStep(Math.max(0, Math.min(maxStep, s)));
  }

  const hits = step === null ? [] : RUNS.map((r) => ({ r, i: nearest(r, step) })).filter((h) => h.i !== null);
  const hx = hits.length ? hits[0].r.points[hits[0].i!][0] : 0;
  const summary = RUNS.map((r) => `${r.label} 마지막 100 step 평균 ${r.smooth[r.smooth.length - 1].toFixed(3)}`).join(", ");

  return (
    <figure className="m-0">
      <div className="relative">
        <svg
          ref={ref}
          viewBox={`0 0 ${W} ${H}`}
          className="block h-auto w-full touch-none"
          role="img"
          aria-label={`학습 Loss 비교: ${summary}`}
          onPointerMove={onMove}
          onPointerLeave={() => setStep(null)}
        >
          {[0, 0.1, 0.2, 0.3, 0.4].map((t) => (
            <g key={t}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} stroke="var(--color-paper-shade)" strokeWidth={1} />
              <text x={PAD.l - 8} y={y(t)} dy="0.32em" textAnchor="end" fontSize={11} fill="var(--color-ink-mute)">
                {t.toFixed(1)}
              </text>
            </g>
          ))}
          {[0, 250, 500, 750, 1000, 1250].filter((s) => s <= maxStep).map((s) => (
            <text key={s} x={x(s)} y={H - 8} textAnchor="middle" fontSize={11} fill="var(--color-ink-mute)">
              {s}
            </text>
          ))}
          {RUNS.map((r) => (
            <path key={`${r.id}-smooth`} d={path(r, r.smooth)} fill="none" stroke="var(--color-ink)" strokeWidth={2}
              strokeDasharray={r.dash} strokeLinejoin="round" />
          ))}
          {hits.length > 0 && (
            <g pointerEvents="none">
              <line x1={x(hx)} x2={x(hx)} y1={PAD.t} y2={H - PAD.b} stroke="var(--color-ink)" strokeDasharray="2 3" opacity={0.6} />
              {hits.map(({ r, i }) => (
                <circle key={r.id} cx={x(r.points[i!][0])} cy={y(r.smooth[i!])} r={4.5} fill={r.dash ? "var(--color-paper)" : "var(--color-ink)"}
                  stroke="var(--color-ink)" strokeWidth={2} />
              ))}
            </g>
          )}
        </svg>
        {hits.length > 0 && (
          <div
            className="pointer-events-none absolute top-1 rounded-sm bg-ink px-2 py-1 text-[12px] leading-snug whitespace-nowrap text-paper"
            style={{ left: `${(x(hx) / W) * 100}%`, transform: `translateX(${hx > maxStep * 0.55 ? "-105%" : "8px"})` }}
          >
            step {hx}
            {hits.map(({ r, i }) => (
              <div key={r.id}>
                {r.label} {r.smooth[i!].toFixed(3)}
              </div>
            ))}
          </div>
        )}
      </div>
      <figcaption className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-[12px] text-ink-mute">
        {RUNS.map((r) => (
          <span key={r.id} className="flex items-center gap-1.5">
            <svg width="22" height="4" aria-hidden>
              <line x1="0" x2="22" y1="2" y2="2" stroke="var(--color-ink)" strokeWidth="2" strokeDasharray={r.dash} />
            </svg>
            {r.label}: {r.smooth[r.smooth.length - 1].toFixed(3)}
          </span>
        ))}
        <span>100 step 이동평균</span>
      </figcaption>
    </figure>
  );
}
