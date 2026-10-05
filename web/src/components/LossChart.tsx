import { useMemo, useRef, useState } from "react";
import loss from "../data/loss.json";

const W = 640;
const H = 240;
const PAD = { l: 44, r: 16, t: 14, b: 30 };
const WINDOW = 10;

const points = loss as [number, number][];
const smooth = points.map((_, i) => {
  const s = points.slice(Math.max(0, i - WINDOW + 1), i + 1);
  return s.reduce((a, [, v]) => a + v, 0) / s.length;
});

export function LossChart() {
  const ref = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);
  const maxStep = points[points.length - 1][0];
  const maxY = 0.45;
  const x = (s: number) => PAD.l + (s / maxStep) * (W - PAD.l - PAD.r);
  const y = (v: number) => PAD.t + (1 - v / maxY) * (H - PAD.t - PAD.b);

  const rawPath = useMemo(() => points.map(([s, v], i) => `${i ? "L" : "M"}${x(s)},${y(v)}`).join(""), []);
  const smoothPath = useMemo(() => points.map(([s], i) => `${i ? "L" : "M"}${x(s)},${y(smooth[i])}`).join(""), []);

  function onMove(e: React.PointerEvent<SVGSVGElement>) {
    const box = ref.current!.getBoundingClientRect();
    const sx = ((e.clientX - box.left) / box.width) * W;
    const step = ((sx - PAD.l) / (W - PAD.l - PAD.r)) * maxStep;
    let best = 0;
    for (let i = 1; i < points.length; i++) if (Math.abs(points[i][0] - step) < Math.abs(points[best][0] - step)) best = i;
    setHover(best);
  }

  const h = hover !== null ? { step: points[hover][0], v: points[hover][1], s: smooth[hover] } : null;

  return (
    <figure className="m-0">
      <div className="relative">
        <svg
          ref={ref}
          viewBox={`0 0 ${W} ${H}`}
          className="block h-auto w-full touch-none"
          role="img"
          aria-label={`학습 Loss: step 10에서 ${points[0][1].toFixed(3)}, 마지막 100 step 평균 ${smooth[smooth.length - 1].toFixed(3)}`}
          onPointerMove={onMove}
          onPointerLeave={() => setHover(null)}
        >
          {[0, 0.1, 0.2, 0.3, 0.4].map((t) => (
            <g key={t}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} stroke="var(--color-paper-shade)" strokeWidth={1} />
              <text x={PAD.l - 8} y={y(t)} dy="0.32em" textAnchor="end" fontSize={11} fill="var(--color-ink-mute)">
                {t.toFixed(1)}
              </text>
            </g>
          ))}
          {[0, 250, 500, 750, 1000].map((s) => (
            <text key={s} x={x(s)} y={H - 8} textAnchor="middle" fontSize={11} fill="var(--color-ink-mute)">
              {s}
            </text>
          ))}
          <path d={rawPath} fill="none" stroke="var(--color-ink-mute)" strokeWidth={1.25} strokeOpacity={0.55} />
          <path d={smoothPath} fill="none" stroke="var(--color-ink)" strokeWidth={2} strokeLinejoin="round" />
          <circle cx={x(points[0][0])} cy={y(points[0][1])} r={4} fill="var(--color-ink)" stroke="var(--color-paper)" strokeWidth={2} />
          {h && (
            <g pointerEvents="none">
              <line x1={x(h.step)} x2={x(h.step)} y1={PAD.t} y2={H - PAD.b} stroke="var(--color-ink)" strokeDasharray="2 3" />
              <circle cx={x(h.step)} cy={y(h.s)} r={4.5} fill="var(--color-ink)" stroke="var(--color-paper)" strokeWidth={2} />
            </g>
          )}
        </svg>
        {h && (
          <div
            className="pointer-events-none absolute top-1 rounded-sm bg-ink px-2 py-1 text-[12px] leading-snug whitespace-nowrap text-paper"
            style={{ left: `${(x(h.step) / W) * 100}%`, transform: `translateX(${h.step > maxStep * 0.6 ? "-105%" : "8px"})` }}
          >
            step {h.step} · loss {h.v.toFixed(3)}
            <br />
            100 step 평균 {h.s.toFixed(3)}
          </div>
        )}
      </div>
      <figcaption className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-[12px] text-ink-mute">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-[2px] w-5 bg-ink" aria-hidden /> 100 step 이동평균
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-[1.5px] w-5 bg-ink-mute/60" aria-hidden /> 10 step마다 기록한 원본
        </span>
        <span>가로축 training step</span>
      </figcaption>
    </figure>
  );
}
