import { useCallback, useEffect, useRef, useState } from "react";
import { type Database, getDatabases, getHealth, type Health, type ModelKey, runQuery, type RunKey } from "./api";
import { Catalog } from "./components/Catalog";
import { OutputTray } from "./components/OutputTray";
import { compareKeys, PrinterPanel } from "./components/PrinterPanel";
import { StatusBand, type View } from "./components/StatusBand";
import { ZReport } from "./components/ZReport";
import type { Job, Mode } from "./types";

const MAX_JOBS = 12;
const DEFAULT_NAMES: Record<ModelKey, string> = { base: "qwen2.5-coder:3b", ft: "text2sql-ft", ft2: "text2sql-ft-v2", ft3: "text2sql-ft-v3" };
const VOTE_NAME = "5개 후보 (베이스라인 · v3 · 예시 행 · v2 · v1)";

function useHealth() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let alive = true;
    const check = () =>
      getHealth()
        .then((h) => alive && (setHealth(h), setError(false)))
        .catch(() => alive && setError(true));
    check();
    const t = window.setInterval(check, 15000);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, []);
  return { health, error };
}

export default function App() {
  const [view, setView] = useState<View>("counter");
  const { health, error: healthError } = useHealth();
  const [databases, setDatabases] = useState<Database[] | null>(null);
  const [dbError, setDbError] = useState<string | null>(null);
  const [dbId, setDbId] = useState("shop");
  const [mode, setMode] = useState<Mode>("ft");
  const [selfCorrect, setSelfCorrect] = useState(false);
  const [question, setQuestion] = useState("");
  const [pickedId, setPickedId] = useState<number | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const counter = useRef(0);
  const trayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getDatabases()
      .then((dbs) => {
        setDatabases(dbs);
        if (dbs.length && !dbs.some((d) => d.id === "shop")) setDbId(dbs[0].id);
      })
      .catch((e: Error) => setDbError(e.message));
  }, []);

  const update = useCallback((id: number, patch: Partial<Job>) => {
    setJobs((js) => js.map((j) => (j.id === id ? { ...j, ...patch } : j)));
  }, []);

  const busy = jobs.some((j) => j.status === "printing" || j.status === "queued");
  const active = jobs.find((j) => j.status === "printing") ?? null;
  const last = jobs.find((j) => j.status === "done") ?? null;

  async function print() {
    const keys: RunKey[] = mode === "compare" ? compareKeys(health) : [mode];
    const now = Date.now();
    const pairId = keys.length > 1 ? now : null;
    const created: Job[] = keys.map((k, i) => ({
      id: now + i,
      no: ++counter.current,
      pairId,
      dbId,
      modelKey: k,
      modelName: k === "vote" ? VOTE_NAME : (health?.models[k]?.name ?? DEFAULT_NAMES[k]),
      question: question.trim(),
      selfCorrect: selfCorrect && k !== "vote",
      startedAt: now,
      status: i === 0 ? "printing" : "queued",
    }));
    setJobs((js) => [...created, ...js].slice(0, MAX_JOBS));
    // 좁은 화면에서는 출력함이 조작판 아래에 있으므로 인쇄되는 영수증으로 내려 준다
    window.setTimeout(() => {
      const top = trayRef.current?.getBoundingClientRect().top ?? 0;
      if (top > window.innerHeight * 0.6) trayRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);

    // CPU 한 대에서 두 모델을 동시에 돌리면 둘 다 느려지므로 차례로 인쇄한다
    for (const [i, job] of created.entries()) {
      const startedAt = i === 0 ? job.startedAt : Date.now();
      if (i > 0) update(job.id, { status: "printing", startedAt });
      try {
        const result = await runQuery({ db_id: job.dbId, question: job.question, model: job.modelKey, self_correct: job.selfCorrect });
        update(job.id, { status: "done", result });
      } catch (e) {
        update(job.id, { status: "failed", failure: (e as Error).message });
      }
    }
  }

  const dbLabel = (id: string) => (id === "shop" ? "shop (한국어 쇼핑몰)" : `${id} (Spider)`);

  return (
    <div className="min-h-[100dvh]">
      <StatusBand view={view} onViewChange={setView} active={active} last={last} health={health} healthError={healthError} />

      {view === "counter" ? (
        <main className="mx-auto grid max-w-[1440px] items-start gap-10 px-4 py-8 md:px-8 md:py-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-14">
          <h1 className="sr-only">질의 영수증: 한국어 질문을 SQL로 바꿔 실행하는 로컬 LLM 데모</h1>
          <div className="flex flex-col gap-10 lg:sticky lg:top-24">
            <PrinterPanel
              databases={databases}
              dbError={dbError}
              dbId={dbId}
              onDbChange={(id) => {
                setDbId(id);
                setPickedId(null);
              }}
              mode={mode}
              onModeChange={setMode}
              selfCorrect={selfCorrect}
              onSelfCorrectChange={setSelfCorrect}
              question={question}
              onQuestionChange={(q) => {
                setQuestion(q);
                setPickedId(null);
              }}
              onPrint={print}
              busy={busy}
              health={health}
            />
            {dbId === "shop" && (
              <Catalog
                selectedId={pickedId}
                onPick={(item) => {
                  setQuestion(item.question);
                  setPickedId(item.id);
                }}
              />
            )}
          </div>
          <div ref={trayRef} className="scroll-mt-20 min-w-0">
            <OutputTray jobs={jobs} dbLabel={dbLabel} />
          </div>
        </main>
      ) : (
        <main>
          <h1 className="sr-only">정산 리포트: 평가 결과</h1>
          <ZReport />
        </main>
      )}
    </div>
  );
}
