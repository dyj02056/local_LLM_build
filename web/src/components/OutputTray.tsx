import { AnimatePresence, motion } from "motion/react";
import { sameRows } from "../format";
import { type Job, MODEL_LABEL } from "../types";
import { Receipt } from "./Receipt";

type Group = { key: number; jobs: Job[] };

function groupJobs(jobs: Job[]): Group[] {
  const groups: Group[] = [];
  for (const j of jobs) {
    const g = j.pairId !== null ? groups.find((x) => x.key === j.pairId) : undefined;
    if (g) g.jobs.push(j);
    else groups.push({ key: j.pairId ?? -j.id, jobs: [j] });
  }
  return groups;
}

/** 비교 결과 꼬리표: 영수증들의 결과 행이 같은지 (정답 여부는 모름) */
function CompareTag({ jobs }: { jobs: Job[] }) {
  if (jobs.some((j) => j.status !== "done" && j.status !== "failed")) return null;
  const ok = jobs.filter((j) => j.result && !j.result.error);
  const failed = jobs.filter((j) => !j.result || j.result.error).map((j) => MODEL_LABEL[j.modelKey]);
  // 같은 결과를 낸 모델끼리 묶는다
  const groups: Job[][] = [];
  for (const j of ok) {
    const g = groups.find((x) => sameRows(x[0].result!.rows, j.result!.rows));
    if (g) g.push(j);
    else groups.push([j]);
  }
  let text: string;
  let strong = false;
  if (ok.length < 2) {
    text = "실행에 성공한 영수증이 2장 미만이라 결과를 비교할 수 없습니다";
  } else if (groups.length === 1) {
    text = `${ok.length}개 모델의 결과 행이 모두 같습니다`;
  } else {
    text = `결과 행이 갈립니다: ${groups.map((g) => g.map((j) => MODEL_LABEL[j.modelKey]).join(", ")).join(" / ")}`;
    strong = true;
  }
  if (failed.length && ok.length >= 2) text += ` (실행 실패: ${failed.join(", ")})`;
  return (
    <p className={`font-receipt text-[13px] ${strong ? "text-thermal-soft" : "text-counter-mute"}`}>
      비교 · {text}
    </p>
  );
}

export function OutputTray({ jobs, dbLabel }: { jobs: Job[]; dbLabel: (id: string) => string }) {
  const groups = groupJobs(jobs);
  return (
    <section aria-label="출력함" className="flex min-w-0 flex-col">
      {/* 프린터 출력구 */}
      <div className="relative h-3 rounded-full bg-slot shadow-[inset_0_2px_3px_rgb(0_0_0/0.6)]" aria-hidden />

      {groups.length === 0 ? (
        <div className="flex flex-col gap-3 px-1 pt-10">
          <p className="text-lg font-semibold text-counter-ink">출력된 영수증이 없습니다</p>
          <p className="max-w-[52ch] leading-relaxed text-counter-mute">
            왼쪽에서 문제 칸을 누르거나 질문을 직접 쓰고 인쇄를 누르세요. 모델이 쓴 SQL이 읽기 전용 DB에서 실행되고, 결과와 걸린
            시간이 영수증으로 나옵니다.
          </p>
          <p className="max-w-[52ch] leading-relaxed text-counter-mute">
            '모두 비교'를 고르면 베이스라인, 파인튜닝 v1, v2의 영수증이 차례로 인쇄되고 결과가 같은지 표시됩니다.
          </p>
        </div>
      ) : (
        <ol className="flex flex-col gap-10 pt-0">
          <AnimatePresence initial={false}>
            {groups.map((g) => (
              <motion.li
                key={g.key}
                layout
                initial={{ y: -32, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ type: "spring", stiffness: 140, damping: 22 }}
                className="flex flex-col gap-3"
              >
                <div className={`grid items-start gap-5 ${g.jobs.length > 1 ? "lg:grid-cols-2" : ""}`}>
                  {g.jobs.map((j) => (
                    <Receipt key={j.id} job={j} dbLabel={dbLabel(j.dbId)} />
                  ))}
                </div>
                {g.jobs.length > 1 && <CompareTag jobs={g.jobs} />}
              </motion.li>
            ))}
          </AnimatePresence>
        </ol>
      )}
    </section>
  );
}
