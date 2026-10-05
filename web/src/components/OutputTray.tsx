import { AnimatePresence, motion } from "motion/react";
import { sameRows } from "../format";
import type { Job } from "../types";
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

/** 비교 결과 꼬리표: 두 영수증의 결과 행이 같은지 */
function CompareTag({ jobs }: { jobs: Job[] }) {
  const [a, b] = jobs;
  if (!a?.result || !b?.result) return null;
  let text: string;
  let strong = false;
  if (a.result.error || b.result.error) {
    text = "한쪽 이상이 실행에 실패해 결과를 비교할 수 없습니다";
  } else if (sameRows(a.result.rows, b.result.rows)) {
    text = "두 모델의 결과 행이 같습니다";
  } else {
    text = "두 모델의 결과 행이 다릅니다";
    strong = true;
  }
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
            '둘 다 비교'를 고르면 베이스라인과 파인튜닝 영수증이 나란히 인쇄됩니다.
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
