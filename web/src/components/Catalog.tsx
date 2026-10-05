import { useMemo, useState } from "react";
import type { ModelKey } from "../api";
import rawCatalog from "../data/korean_catalog.json";
import { MODEL_KEYS, MODEL_LABEL } from "../types";

type Item = { id: number; level: string; question: string } & Partial<Record<ModelKey, boolean>>;
const catalog = rawCatalog as Item[];
const LEVELS = ["전체", "쉬움", "보통", "어려움"] as const;
// 실측 결과가 있는 모델만 (내보낸 데이터 기준)
const MEASURED = MODEL_KEYS.filter((k) => catalog.some((c) => c[k] !== undefined));

/** 정답은 실선, 오답은 점선. 색이 아니라 인쇄 모양으로 구분한다. */
function Mark({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      aria-label={`${label} ${ok ? "정답" : "오답"}`}
      className={`block h-[3px] flex-1 ${ok ? "bg-current" : "bg-[radial-gradient(circle,currentColor_1px,transparent_1.3px)] bg-[length:4px_3px] bg-repeat-x opacity-70"}`}
    />
  );
}

function verdict(item: Item) {
  return MEASURED.map((k) => `${MODEL_LABEL[k]} ${item[k] ? "정답" : "오답"}`).join(" · ");
}

export function Catalog({ selectedId, onPick }: { selectedId: number | null; onPick: (item: Item) => void }) {
  const [level, setLevel] = useState<(typeof LEVELS)[number]>("전체");
  const [peek, setPeek] = useState<Item | null>(null);
  const items = useMemo(() => (level === "전체" ? catalog : catalog.filter((c) => c.level === level)), [level]);
  const scores = MEASURED.map((k) => ({ k, n: items.filter((c) => c[k]).length }));
  const shown = peek ?? catalog.find((c) => c.id === selectedId) ?? null;

  return (
    <section aria-labelledby="catalog-title" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-2">
        <h2 id="catalog-title" className="text-sm font-semibold text-counter-ink">
          한국어 평가 문제 100개
        </h2>
        <div role="tablist" aria-label="난이도" className="flex gap-1">
          {LEVELS.map((l) => (
            <button
              key={l}
              role="tab"
              type="button"
              aria-selected={level === l}
              onClick={() => setLevel(l)}
              className={`cursor-pointer rounded px-2.5 py-1 text-[13px] transition-colors ${
                level === l ? "bg-counter-ink text-counter" : "text-counter-mute hover:bg-counter-3 hover:text-counter-ink"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      <p className="font-receipt text-[13px] text-counter-mute">
        {level} {items.length}문제 실측
        {scores.map(({ k, n }) => (
          <span key={k}>
            {" "}· {MODEL_LABEL[k]} <span className="text-counter-ink">{n}</span>
          </span>
        ))}
      </p>

      <ol className="grid grid-cols-10 gap-1" onMouseLeave={() => setPeek(null)}>
        {items.map((item) => {
          const selected = item.id === selectedId;
          return (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => onPick(item)}
                onMouseEnter={() => setPeek(item)}
                onFocus={() => setPeek(item)}
                onBlur={() => setPeek(null)}
                aria-pressed={selected}
                aria-label={`${item.id}번 ${item.level}: ${item.question} (${verdict(item)})`}
                className={`flex aspect-square w-full cursor-pointer flex-col justify-between rounded-[3px] px-1 pt-1 pb-1.5 font-receipt text-[12px] leading-none transition-[background-color,transform] duration-150 active:scale-95 ${
                  selected
                    ? "bg-paper text-ink"
                    : "bg-counter-2 text-counter-mute hover:bg-counter-3 hover:text-counter-ink"
                }`}
              >
                <span className="self-start">{item.id}</span>
                <span className="flex w-full gap-[3px]" aria-hidden>
                  {MEASURED.map((k) => (
                    <Mark key={k} ok={!!item[k]} label={MODEL_LABEL[k]} />
                  ))}
                </span>
              </button>
            </li>
          );
        })}
      </ol>

      <div className="min-h-[4.5rem] rounded-md border border-counter-line px-3.5 py-2.5" aria-live="polite">
        {shown ? (
          <>
            <p className="font-receipt text-[12px] text-counter-mute">
              {shown.id}번 · {shown.level} · {verdict(shown)}
            </p>
            <p className="mt-1 text-[15px] leading-snug text-counter-ink">{shown.question}</p>
          </>
        ) : (
          <p className="text-sm leading-relaxed text-counter-mute">
            칸 아래 막대는 실측 채점 결과입니다. 왼쪽부터 {MEASURED.map((k) => MODEL_LABEL[k]).join(", ")} 순서이고 실선이
            정답, 점선이 오답입니다. 칸을 누르면 질문이 입력됩니다.
          </p>
        )}
      </div>
    </section>
  );
}
