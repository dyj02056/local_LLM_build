import { Printer } from "@phosphor-icons/react";
import { useId } from "react";
import type { Database, Health, ModelKey } from "../api";
import { MODEL_KEYS, MODEL_LABEL, type Mode } from "../types";

type Props = {
  databases: Database[] | null;
  dbError: string | null;
  dbId: string;
  onDbChange: (id: string) => void;
  mode: Mode;
  onModeChange: (m: Mode) => void;
  selfCorrect: boolean;
  onSelfCorrectChange: (v: boolean) => void;
  question: string;
  onQuestionChange: (q: string) => void;
  onPrint: () => void;
  busy: boolean;
  health: Health | null;
};

const MODES: { id: Mode; label: string; hint: string }[] = [
  { id: "base", label: MODEL_LABEL.base, hint: "파인튜닝 전" },
  { id: "ft", label: MODEL_LABEL.ft, hint: "Spider" },
  { id: "ft2", label: MODEL_LABEL.ft2, hint: "Spider+한국어" },
  { id: "ft3", label: MODEL_LABEL.ft3, hint: "JOIN 균형" },
  { id: "vote", label: MODEL_LABEL.vote, hint: "5개 후보 · 약 5배 느림" },
  { id: "compare", label: "모두 비교", hint: "설치된 모델 전부" },
];

function modeUnavailable(m: Mode, health: Health | null): string | null {
  if (!health || !health.ollama) return null; // 연결 문제는 상태 띠에서 따로 알린다
  if (m === "compare") {
    return compareKeys(health).length < 2 ? "비교하려면 모델이 2개 이상 Ollama에 있어야 합니다" : null;
  }
  if (m === "vote") {
    const missing = MODEL_KEYS.filter((k) => !health.models[k].installed).map((k) => health.models[k].name);
    return missing.length ? `다수결에는 ${missing.join(", ")} 모델이 필요한데 Ollama에 없습니다` : null;
  }
  return health.models[m].installed ? null : `${health.models[m].name} 모델이 Ollama에 없습니다`;
}

/** 비교 모드에서 인쇄할 모델: 설치된 것만 */
export function compareKeys(health: Health | null): ModelKey[] {
  return MODEL_KEYS.filter((k) => !health || health.models[k]?.installed);
}

export function PrinterPanel(p: Props) {
  const ids = { db: useId(), q: useId(), qHelp: useId(), sc: useId(), scHelp: useId() };
  const korean = p.dbId === "shop";
  const blocked = modeUnavailable(p.mode, p.health);
  const canPrint = !p.busy && p.question.trim().length > 0 && !!p.dbId && !blocked;

  return (
    <form
      className="flex flex-col gap-6"
      onSubmit={(e) => {
        e.preventDefault();
        if (canPrint) p.onPrint();
      }}
    >
      <div className="flex flex-col gap-2">
        <label htmlFor={ids.db} className="text-sm font-semibold text-counter-ink">
          데이터베이스
        </label>
        <select
          id={ids.db}
          value={p.dbId}
          onChange={(e) => p.onDbChange(e.target.value)}
          disabled={!p.databases?.length}
          className="h-11 cursor-pointer rounded-md border border-counter-line bg-counter-2 px-3 text-[15px] text-counter-ink transition-colors hover:border-counter-mute disabled:cursor-not-allowed disabled:opacity-60"
        >
          {!p.databases && <option>불러오는 중</option>}
          {p.databases?.some((d) => d.group === "korean") && (
            <optgroup label="한국어">
              <option value="shop">shop · 가상 쇼핑몰 (질문 100개 실측)</option>
            </optgroup>
          )}
          {p.databases?.some((d) => d.group === "spider") && (
            <optgroup label="Spider dev (영어 질문)">
              {p.databases
                .filter((d) => d.group === "spider")
                .map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.id}
                  </option>
                ))}
            </optgroup>
          )}
        </select>
        {p.dbError ? (
          <p className="text-sm text-thermal-soft">DB 목록을 불러오지 못했습니다: {p.dbError}</p>
        ) : (
          <p className="text-sm text-counter-mute">
            {korean ? "테이블 6개, 주문 800건. 값은 한국어입니다." : "Spider 평가용 DB입니다. 질문은 영어로 쓰세요."}
          </p>
        )}
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="mb-2 text-sm font-semibold text-counter-ink">모델</legend>
        <div className="grid grid-cols-2 rounded-md border border-counter-line bg-counter-2 p-1 sm:grid-cols-4">
          {MODES.map((m) => {
            const active = p.mode === m.id;
            return (
              <label
                key={m.id}
                className={`relative flex cursor-pointer flex-col items-center rounded-[5px] px-1 py-2 text-center transition-colors duration-200 ${
                  m.id === "compare" || m.id === "vote" ? "sm:col-span-2" : ""
                } ${
                  active ? "bg-paper text-ink" : "text-counter-mute hover:bg-counter-3 hover:text-counter-ink"
                }`}
              >
                <input
                  type="radio"
                  name="mode"
                  value={m.id}
                  checked={active}
                  onChange={() => p.onModeChange(m.id)}
                  className="peer sr-only"
                />
                <span className="text-[15px] font-semibold">{m.label}</span>
                <span className={`mt-0.5 font-receipt text-[11px] ${active ? "text-ink-mute" : ""}`}>{m.hint}</span>
                <span className="pointer-events-none absolute inset-0 rounded-[5px] peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-counter-ink" />
              </label>
            );
          })}
        </div>
        {p.mode === "vote" && !blocked && (
          <p className="text-sm text-counter-mute">
            베이스라인, v3, 베이스라인 + 예시 행, v2, v1이 쓴 SQL 5개를 실행해 결과 행이 같은 쪽이 가장 많은 SQL을 고릅니다. 동률이면
            앞의 후보가 이깁니다. 모델을 5번 돌리므로 모델이 메모리에 올라 있어도 25~30초, 처음에는 모델을 올리느라 1~2분 걸립니다.
          </p>
        )}
        {blocked && <p className="text-sm text-thermal-soft">{blocked}. README의 등록 방법을 확인하세요.</p>}
      </fieldset>

      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor={ids.sc} className="cursor-pointer text-sm font-semibold text-counter-ink">
            자동수정 (self-correction)
          </label>
          <p id={ids.scHelp} className="max-w-[46ch] text-sm text-counter-mute">
            SQL이 실행 오류를 내면 오류 메시지를 보여 주고 최대 2번 다시 쓰게 합니다. 정답은 보지 않습니다.
            {p.mode === "vote" && " 다수결에서는 쓰지 않습니다."}
          </p>
        </div>
        <button
          id={ids.sc}
          type="button"
          role="switch"
          aria-checked={p.selfCorrect && p.mode !== "vote"}
          aria-describedby={ids.scHelp}
          disabled={p.mode === "vote"}
          onClick={() => p.onSelfCorrectChange(!p.selfCorrect)}
          className={`relative mt-0.5 h-7 w-12 shrink-0 cursor-pointer rounded-full border transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-40 ${
            p.selfCorrect && p.mode !== "vote" ? "border-paper bg-paper" : "border-counter-line bg-counter-2 hover:border-counter-mute"
          }`}
        >
          <span
            className={`absolute top-1/2 left-1 size-5 -translate-y-1/2 rounded-full transition-transform duration-300 ease-out-expo ${
              p.selfCorrect && p.mode !== "vote" ? "translate-x-5 bg-ink" : "bg-counter-mute"
            }`}
          />
        </button>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor={ids.q} className="text-sm font-semibold text-counter-ink">
          질문
        </label>
        <textarea
          id={ids.q}
          value={p.question}
          onChange={(e) => p.onQuestionChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              if (canPrint) p.onPrint();
            }
          }}
          rows={3}
          maxLength={1000}
          aria-describedby={ids.qHelp}
          placeholder={korean ? "예: 취소된 주문을 빼고 카테고리별 매출을 높은 순으로 보여 줘" : "e.g. How many singers do we have?"}
          className="resize-y rounded-md border border-counter-line bg-counter-2 px-3.5 py-3 text-[16px] leading-relaxed text-counter-ink placeholder:text-counter-mute/80 hover:border-counter-mute focus:border-counter-ink focus:outline-none"
        />
        <p id={ids.qHelp} className="text-sm text-counter-mute">
          Ctrl + Enter로도 인쇄합니다. 첫 질문은 모델을 메모리에 올리느라 20초쯤 걸릴 수 있어요.
        </p>
      </div>

      <button
        type="submit"
        disabled={!canPrint}
        className="flex h-13 cursor-pointer items-center justify-center gap-2.5 rounded-md bg-paper text-[17px] font-bold text-ink transition-[transform,background-color] duration-200 ease-out-expo hover:bg-paper-shade active:translate-y-px active:scale-[0.99] disabled:cursor-not-allowed disabled:bg-counter-3 disabled:text-counter-mute"
      >
        <Printer size={22} weight="bold" aria-hidden />
        {p.busy ? "인쇄 중" : p.mode === "compare" ? `${compareKeys(p.health).length}장 인쇄` : "인쇄"}
      </button>
    </form>
  );
}
