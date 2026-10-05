import { motion } from "motion/react";
import type { Health } from "../api";
import { seconds } from "../format";
import { MODEL_LABEL, type Job } from "../types";
import { Elapsed } from "./Elapsed";

export type View = "counter" | "report";

function Logo() {
  return (
    <svg viewBox="0 0 32 32" className="size-7" aria-hidden>
      <path d="M8 4h16v23l-2.67-1.7L18.67 27 16 25.3 13.33 27l-2.66-1.7L8 27z" fill="var(--color-paper)" />
      <path d="M11.5 10h9M11.5 14h9" stroke="var(--color-ink)" strokeWidth="1.7" strokeLinecap="round" /><path d="M11.5 18h5.5" stroke="var(--color-thermal)" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

function Stage({ active, last }: { active: Job | null; last: Job | null }) {
  if (active) {
    return (
      <span className="flex min-w-0 items-center gap-2.5">
        <motion.span
          aria-hidden
          className="size-2 shrink-0 rounded-[1px] bg-thermal-soft"
          animate={{ opacity: [1, 0.25, 1] }}
          transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
        />
        <span className="truncate">
          {active.no}번 · {MODEL_LABEL[active.modelKey]} SQL 생성 중
        </span>
        <Elapsed since={active.startedAt} className="font-receipt text-counter-ink" />
      </span>
    );
  }
  if (last?.result) {
    const total = last.result.generation_ms + last.result.execution_ms;
    return (
      <span className="truncate">
        대기 중 · 마지막 {last.no}번 합계 <span className="font-receipt text-counter-ink">{seconds(total)}</span>
      </span>
    );
  }
  return <span>대기 중</span>;
}

function Connection({ health, error }: { health: Health | null; error: boolean }) {
  if (error || (health && !health.ollama)) {
    return <span className="text-thermal-soft">Ollama 연결 안 됨</span>;
  }
  if (!health) return <span>연결 확인 중</span>;
  const ready = Object.values(health.models).filter((m) => m.installed).length;
  return (
    <span>
      Ollama 연결됨 · 모델 {ready}/2
    </span>
  );
}

export function StatusBand(p: {
  view: View;
  onViewChange: (v: View) => void;
  active: Job | null;
  last: Job | null;
  health: Health | null;
  healthError: boolean;
}) {
  const tabs: { id: View; label: string }[] = [
    { id: "counter", label: "계산대" },
    { id: "report", label: "정산 리포트" },
  ];
  return (
    <header className="sticky top-0 z-20 border-b border-counter-line bg-counter">
      <div className="mx-auto flex h-14 max-w-[1440px] items-center gap-4 px-4 md:gap-8 md:px-8">
        <div className="flex shrink-0 items-center gap-2.5">
          <Logo />
          <span className="hidden text-[17px] font-bold tracking-tight sm:inline">질의 영수증</span>
        </div>
        <nav aria-label="화면" className="flex shrink-0 gap-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              aria-current={p.view === t.id ? "page" : undefined}
              onClick={() => p.onViewChange(t.id)}
              className={`cursor-pointer rounded px-3 py-1.5 text-[15px] transition-colors ${
                p.view === t.id ? "bg-counter-3 font-semibold text-counter-ink" : "text-counter-mute hover:text-counter-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="ml-auto flex min-w-0 items-center gap-6 text-sm text-counter-mute" role="status">
          <span className="hidden min-w-0 md:flex">
            <Stage active={p.active} last={p.last} />
          </span>
          <span className="shrink-0">
            <Connection health={p.health} error={p.healthError} />
          </span>
        </div>
      </div>
      {p.active && (
        <div className="border-t border-counter-line px-4 py-2 text-sm text-counter-mute md:hidden">
          <Stage active={p.active} last={p.last} />
        </div>
      )}
    </header>
  );
}
