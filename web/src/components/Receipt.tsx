import { motion } from "motion/react";
import { type ReactNode, useState } from "react";
import { formatCell, isNumeric, seconds, stamp } from "../format";
import { sqlLines } from "../sqlLines";
import { MODEL_LABEL, type Job } from "../types";
import { Elapsed } from "./Elapsed";

const PRINT = { duration: 0.42, ease: [0.16, 1, 0.3, 1] as const };
const ROW_PREVIEW = 12;

/** 한 구역이 위에서 아래로 인쇄되듯 드러난다 */
function Printed({ i, children }: { i: number; children: ReactNode }) {
  return (
    <motion.div
      initial={{ clipPath: "inset(0 0 100% 0)", opacity: 0.4 }}
      animate={{ clipPath: "inset(0 0 0% 0)", opacity: 1 }}
      transition={{ ...PRINT, delay: i * 0.11 }}
    >
      {children}
    </motion.div>
  );
}

function Rule({ kind = "dash" }: { kind?: "dash" | "double" }) {
  return <div className={`my-3 ${kind === "dash" ? "rule-dash" : "rule-double"}`} aria-hidden />;
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div className="mb-1.5 inline-block bg-ink px-1.5 text-[0.8em] leading-[1.6] font-bold tracking-wider text-paper">
      {children}
    </div>
  );
}

function Meta({ k, v }: { k: string; v: ReactNode }) {
  return (
    <div className="grid grid-cols-[max-content_1fr] gap-x-[2ch]">
      <span className="w-[8ch] whitespace-nowrap text-ink-mute">{k}</span>
      <span className="min-w-0 [overflow-wrap:anywhere]">{v}</span>
    </div>
  );
}

/** SQL을 절마다 한 줄씩. 긴 줄은 단어 경계에서 접고, 이어지는 줄은 들여 쓴다. */
function Sql({ sql, voided = false }: { sql: string; voided?: boolean }) {
  return (
    <div className={voided ? "text-thermal line-through decoration-thermal decoration-[1.5px]" : ""}>
      {sqlLines(sql).map((line, i) => (
        <p key={i} className="pl-[2ch] -indent-[2ch] [overflow-wrap:anywhere]">
          {line}
        </p>
      ))}
    </div>
  );
}

function ResultTable({ columns, rows, truncated }: { columns: string[]; rows: unknown[][]; truncated: boolean }) {
  const [all, setAll] = useState(false);
  const shown = all ? rows : rows.slice(0, ROW_PREVIEW);
  if (rows.length === 0) {
    return <p className="text-ink-mute">결과 0행 (조건에 맞는 데이터가 없습니다)</p>;
  }
  return (
    <div>
      <div className="-mx-1 overflow-x-auto px-1 pb-1">
        <table className="w-max min-w-full border-collapse text-left">
          <thead>
            <tr>
              {columns.map((c, i) => (
                <th
                  key={i}
                  className={`border-b-[1.5px] border-dashed border-ink/50 pr-[2ch] pb-1 font-bold whitespace-nowrap last:pr-0 ${isNumeric(rows[0]?.[i]) ? "text-right" : ""}`}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shown.map((r, i) => (
              <tr key={i}>
                {r.map((v, j) => (
                  <td
                    key={j}
                    title={String(v)}
                    className={`pt-1 pr-[2ch] align-top whitespace-nowrap last:pr-0 ${isNumeric(v) ? "text-right" : ""} ${v === null ? "text-ink-mute" : ""}`}
                  >
                    {formatCell(v)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(rows.length > ROW_PREVIEW || truncated) && (
        <div className="mt-2 flex items-center justify-between gap-2 text-ink-mute">
          <span>
            {all ? `${rows.length}행 전부` : `${ROW_PREVIEW}행 표시 · 외 ${rows.length - ROW_PREVIEW}행`}
            {truncated && " (200행에서 잘림)"}
          </span>
          {rows.length > ROW_PREVIEW && (
            <button
              type="button"
              onClick={() => setAll((a) => !a)}
              className="cursor-pointer underline decoration-dotted underline-offset-4 hover:text-ink active:translate-y-px"
            >
              {all ? "접기" : "모두 보기"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export function Receipt({ job, dbLabel }: { job: Job; dbLabel: string }) {
  const r = job.result;
  const done = job.status === "done" && r;
  let section = 0;

  return (
    <article
      aria-label={`영수증 ${job.no}번, ${MODEL_LABEL[job.modelKey]}`}
      aria-busy={job.status === "printing" || job.status === "queued"}
      className="receipt-paper w-full max-w-[calc(42ch+3rem)] px-6 pt-6 pb-9 text-[13.5px] leading-[1.55]"
    >
      <Printed i={section++}>
        <header className="text-center">
          <div className="dh font-bold tracking-[0.6em]">질의영수증</div>
          <div className="mt-1 text-ink-mute">LOCAL TEXT-TO-SQL · OLLAMA CPU</div>
        </header>
        <Rule />
        <Meta k="No." v={String(job.no).padStart(4, "0")} />
        <Meta k="일시" v={stamp(job.startedAt)} />
        <Meta k="DB" v={dbLabel} />
        <Meta
          k="모델"
          v={
            <>
              <span className={job.modelKey !== "base" ? "bg-ink px-1 text-paper" : ""}>{MODEL_LABEL[job.modelKey]}</span>{" "}
              {job.modelName}
            </>
          }
        />
        <Meta k="자동수정" v={job.modelKey === "vote" ? "해당 없음" : job.selfCorrect ? "켜짐 (최대 2회)" : "꺼짐"} />
        <Rule />
        <SectionLabel>질문</SectionLabel>
        <p className="break-words whitespace-pre-wrap">{job.question}</p>
        <Rule />
      </Printed>

      {(job.status === "queued" || job.status === "printing") && (
        <div className="space-y-2.5 py-1" role="status">
          <div className="flex items-center justify-between text-ink-mute">
            <span>{job.status === "queued"
                ? "앞 영수증 인쇄를 기다리는 중"
                : job.modelKey === "vote"
                  ? "5개 후보가 차례로 SQL을 쓰는 중"
                  : "모델이 SQL을 쓰는 중"}</span>
            {job.status === "printing" && <Elapsed since={job.startedAt} className="text-ink" />}
          </div>
          <div className="pending-line w-full" />
          <div className="pending-line w-4/5" />
          <div className="pending-line w-3/5" />
        </div>
      )}

      {job.status === "failed" && (
        <Printed i={section++}>
          <SectionLabel>통신 오류</SectionLabel>
          <p className="font-bold text-thermal">{job.failure}</p>
          <p className="mt-2 text-ink-mute">Ollama가 실행 중인지, 모델이 등록돼 있는지 확인한 뒤 다시 인쇄하세요.</p>
        </Printed>
      )}

      {done && (
        <>
          <Printed i={section++}>
            <SectionLabel>SQL</SectionLabel>
            {r.attempts.map((a, i) => (
              <div key={i} className="mb-2.5">
                <Sql sql={a.sql} voided />
                <p className="mt-1 text-thermal">
                  <span className="bg-thermal px-1 text-paper">VOID {i + 1}차</span> {a.error}
                </p>
                {i > 0 && a.sql === r.attempts[i - 1].sql && (
                  <p className="text-thermal">오류를 보고도 직전과 같은 SQL을 다시 썼습니다</p>
                )}
              </div>
            ))}
            <Sql sql={r.sql} />
            {r.attempts.length > 0 && r.sql === r.attempts[r.attempts.length - 1].sql && (
              <p className="mt-1 text-thermal">마지막 시도도 직전과 같은 SQL입니다</p>
            )}
            {r.attempts.length > 0 && !r.error && (
              <p className="mt-1 text-ink-mute">오류 메시지를 보고 {r.attempts.length}번 고쳐 쓴 SQL</p>
            )}
            <Rule />
          </Printed>

          {r.vote && (
            <Printed i={section++}>
              <div className="flex items-baseline justify-between">
                <SectionLabel>후보 투표</SectionLabel>
                <span className="text-ink-mute">
                  {r.vote.votes > 0 ? `${r.vote.votes}/${r.vote.total}표` : "모두 실행 실패"}
                </span>
              </div>
              <ol className="space-y-2">
                {r.vote.candidates.map((c, i) => (
                  <li key={i}>
                    <div className="leader">
                      <span className={c.picked ? "font-bold" : ""}>
                        {c.picked ? "▶ " : ""}
                        {c.label}
                      </span>
                      <span className={c.error ? "text-thermal" : "text-ink-mute"}>
                        {c.group === null ? "오류" : `결과 ${String.fromCharCode(64 + c.group)}`}
                      </span>
                    </div>
                    {c.picked ? null : <Sql sql={c.sql} voided={!!c.error} />}
                    {c.error && <p className="text-thermal">{c.error}</p>}
                  </li>
                ))}
              </ol>
              <p className="mt-2 text-ink-mute">같은 알파벳은 같은 결과 행을 냈다는 뜻입니다. 정답 여부는 알 수 없습니다.</p>
              <Rule />
            </Printed>
          )}

          <Printed i={section++}>
            {r.error ? (
              <>
                <SectionLabel>실행 실패</SectionLabel>
                <p className="font-bold text-thermal">{r.error}</p>
                <p className="mt-1 text-ink-mute">
                  {job.selfCorrect ? "2번 고쳐 써도 실행되지 않았습니다." : "자동수정을 켜면 오류를 보고 다시 써 봅니다."}
                </p>
              </>
            ) : (
              <>
                <div className="flex items-baseline justify-between">
                  <SectionLabel>결과</SectionLabel>
                  <span className="text-ink-mute">{r.rows.length}행</span>
                </div>
                <ResultTable columns={r.columns} rows={r.rows} truncated={r.truncated} />
              </>
            )}
            <Rule />
          </Printed>

          <Printed i={section++}>
            <div className="leader">
              <span>SQL 생성{r.attempts.length > 0 ? ` (수정 ${r.attempts.length}회 포함)` : ""}</span>
              <span>{seconds(r.generation_ms)}</span>
            </div>
            <div className="leader">
              <span>DB 실행</span>
              <span>{seconds(r.execution_ms)}</span>
            </div>
            <Rule kind="double" />
            <div className="leader font-bold">
              <span className="dh">합계</span>
              <span className="dh">{seconds(r.generation_ms + r.execution_ms)}</span>
            </div>
            <div className="mt-4 text-center text-[0.85em] leading-relaxed text-ink-mute">
              읽기 전용 연결 · SELECT만 허용 · 5초 제한
              <br />
              PRAGMA, ATTACH, 쓰기 명령은 DB가 거부합니다
            </div>
          </Printed>
        </>
      )}
    </article>
  );
}
