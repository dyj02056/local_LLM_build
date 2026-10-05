import type { ReactNode } from "react";
import { korean, selfCorrection, spider, training, v2Data } from "../data/report";
import { LossChart } from "./LossChart";

/** 정산 테이프의 한 구역. 구역 사이는 이중선으로 끊는다. */
function Segment({ title, note, children }: { title: string; note?: string; children: ReactNode }) {
  return (
    <section className="[&+&]:mt-8 [&+&]:border-t-[3px] [&+&]:border-double [&+&]:border-ink [&+&]:pt-8">
      <h2 className="inline-block bg-ink px-2 leading-[1.7] font-bold text-paper">{title}</h2>
      {note && <p className="mt-2 text-ink-mute">{note}</p>}
      <div className="mt-5">{children}</div>
    </section>
  );
}

const pct = (v: number) => `${v.toFixed(1)}%`;
const delta = (d: number, unit = "%p") => `${d > 0 ? "+" : ""}${d.toFixed(1)}${unit}`;
const UNDERLINE = "underline decoration-[1.5px] underline-offset-4";
const CHART_COL = "hidden sm:table-cell";

/** 0~100 눈금 위의 전후 비교: 속 빈 점 = 베이스라인, 찬 점 = 파인튜닝 */
function Dumbbell({ base, ft, worse = false }: { base: number; ft: number; worse?: boolean }) {
  const lo = Math.min(base, ft);
  const hi = Math.max(base, ft);
  return (
    <div className="relative h-4 min-w-[110px]" aria-hidden>
      <div className="absolute inset-x-0 top-1/2 border-t border-dashed border-ink/25" />
      <div
        className={`absolute top-1/2 h-[2px] -translate-y-1/2 ${worse ? "bg-thermal" : "bg-ink"}`}
        style={{ left: `${lo}%`, width: `${hi - lo}%` }}
      />
      <span
        className="absolute top-1/2 size-[9px] -translate-x-1/2 -translate-y-1/2 rounded-full border-[1.5px] border-ink bg-paper"
        style={{ left: `${base}%` }}
      />
      <span
        className={`absolute top-1/2 size-[9px] -translate-x-1/2 -translate-y-1/2 rounded-full ${worse ? "bg-thermal" : "bg-ink"}`}
        style={{ left: `${ft}%` }}
      />
    </div>
  );
}

function DumbbellLegend() {
  return (
    <p className="mt-3 hidden flex-wrap gap-x-5 gap-y-1 text-[12px] text-ink-mute sm:flex">
      <span className="flex items-center gap-1.5">
        <span className="inline-block size-[9px] rounded-full border-[1.5px] border-ink" aria-hidden /> 베이스라인
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block size-[9px] rounded-full bg-ink" aria-hidden /> 파인튜닝
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block size-[9px] rounded-full bg-thermal" aria-hidden /> 파인튜닝 후 나빠짐
      </span>
      <span>눈금 0~100%</span>
    </p>
  );
}

const th = "pb-2 pr-4 text-left font-bold whitespace-nowrap border-b-[1.5px] border-dashed border-ink/50 last:pr-0";
const td = "py-1.5 pr-4 whitespace-nowrap last:pr-0";

function ZTape() {
  const s0 = spider.rows[0];
  const s2 = spider.rows[2];
  const line = (k: string, v: ReactNode) => (
    <div className="leader">
      <span>{k}</span>
      <span>{v}</span>
    </div>
  );
  return (
    <section aria-label="정산 요약" className="receipt-paper w-full px-6 pt-6 pb-10 text-[13.5px] leading-[1.6] lg:sticky lg:top-20">
      <div className="text-center">
        <div className="dh font-bold tracking-[0.6em]">Z정산</div>
        <div className="text-ink-mute">평가 결과 일일 마감</div>
      </div>
      <div className="rule-dash my-3" />
      <p className="text-ink-mute">Spider dev {spider.total.toLocaleString()}문제 (영어)</p>
      {line("실행 정확도", `${pct(s0.ex)} → ${pct(s2.ex)}`)}
      {line("SQL 오류율", `${pct(s0.err)} → ${pct(s2.err)}`)}
      {line("평균 응답", `${s0.lat}초 → ${s2.lat}초`)}
      <div className="rule-double my-3" />
      <div className="leader font-bold">
        <span className="dh">파인튜닝 효과</span>
        <span className="dh">{delta(s2.ex - s0.ex)}</span>
      </div>
      <div className="rule-dash my-3" />
      <p className="text-ink-mute">한국어 쇼핑몰 {korean.total}문제 (직접 구축)</p>
      {line("실행 정확도", `${korean.overall.base}% → ${korean.overall.ft}%`)}
      {line("JOIN 2개 이상", `${korean.byJoins[2].base}/14 → ${korean.byJoins[2].ft}/14`)}
      <div className="rule-double my-3" />
      <div className="leader font-bold text-thermal">
        <span className="dh">파인튜닝 효과</span>
        <span className="dh">{delta(korean.overall.ft - korean.overall.base)}</span>
      </div>
      <div className="rule-dash my-3" />
      <p className="text-ink-mute">v2: 한국어 다중 JOIN 940문제 추가 학습</p>
      {line("한국어 정확도 (v1→v2)", `${korean.overall.ft}% → ${korean.overall.ft2}%`)}
      {line("JOIN 2개 이상", `${korean.byJoins[2].ft}/14 → ${korean.byJoins[2].ft2}/14`)}
      {line("Spider (v1→v2)", `${pct(s2.ex)} → ${pct(spider.rows[4].ex)}`)}
      <div className="rule-dash my-3" />
      {line("자동수정 (Spider)", delta(spider.rows[3].ex - s2.ex))}
      {line("학습 Loss", `${training.lossStart.toFixed(3)} → ${training.lossEnd.toFixed(3)}`)}
      <div className="rule-dash my-3" />
      <p className="text-center text-[0.85em] leading-relaxed text-ink-mute">
        모든 숫자는 저장소에 남긴 실측 결과입니다.
        <br />
        재현 방법은 README에 있습니다.
      </p>
    </section>
  );
}

export function ZReport() {
  const bestEx = Math.max(...spider.rows.map((x) => x.ex));
  return (
    <div className="mx-auto grid max-w-[1440px] items-start gap-8 px-4 py-8 md:px-8 md:py-12 lg:grid-cols-[minmax(0,calc(42ch+3rem))_minmax(0,1fr)] lg:gap-12">
      <ZTape />

      {/* 상세 내역: 하나로 이어진 넓은 정산 테이프 */}
      <article
        aria-label="정산 상세"
        className="receipt-paper w-full max-w-[calc(88ch+4rem)] min-w-0 px-5 pt-7 pb-12 text-[13.5px] leading-[1.6] sm:px-8"
      >
        <Segment
          title="Spider dev 실행 정확도"
          note={`영어 질문 ${spider.total.toLocaleString()}문제. 실행 결과가 정답 SQL과 같으면 정답입니다. 자동수정은 실행 오류가 난 문제만 다시 씁니다.`}
        >
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={th}>방식</th>
                  <th className={`${th} text-right`}>정확도</th>
                  <th className={`${th} ${CHART_COL} w-[34%]`} aria-label="정확도 막대" />
                  <th className={`${th} text-right`}>오류율</th>
                  <th className={`${th} text-right`}>응답</th>
                </tr>
              </thead>
              <tbody>
                {spider.rows.map((r) => (
                  <tr key={r.label}>
                    <td className={`${td} whitespace-normal ${r.ex === bestEx ? UNDERLINE : ""}`}>{r.label}</td>
                    <td className={`${td} text-right ${r.ex === bestEx ? UNDERLINE : ""}`}>{pct(r.ex)}</td>
                    <td className={`${td} ${CHART_COL}`}>
                      <div className="h-[7px] bg-paper-shade">
                        <div className="h-full bg-ink" style={{ width: `${r.ex}%` }} />
                      </div>
                    </td>
                    <td className={`${td} text-right`}>{pct(r.err)}</td>
                    <td className={`${td} text-right`}>{r.lat.toFixed(2)}초</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-ink-mute">
            문제별로 보면 {spider.flips.fixed}문제가 새로 맞고 {spider.flips.broken}문제가 새로 틀렸습니다. 부호 검정 z ≈{" "}
            {spider.flips.z}로 우연으로 보기 어려운 차이입니다.
          </p>
        </Segment>

        <Segment title="SQL 유형별 정답률 (Spider)" note="정답 SQL에 들어 있는 구성 요소로 나눴습니다. 한 문제가 여러 유형에 들어갈 수 있습니다.">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={th}>유형</th>
                  <th className={`${th} text-right`}>문제</th>
                  <th className={`${th} text-right`}>전</th>
                  <th className={`${th} text-right`}>후</th>
                  <th className={`${th} text-right`}>변화</th>
                  <th className={`${th} ${CHART_COL} w-[32%]`} aria-label="전후 비교 눈금" />
                </tr>
              </thead>
              <tbody>
                {spider.byType.map((r) => (
                  <tr key={r.type}>
                    <td className={td}>{r.type}</td>
                    <td className={`${td} text-right text-ink-mute`}>{r.n}</td>
                    <td className={`${td} text-right`}>{pct(r.base)}</td>
                    <td className={`${td} text-right`}>{pct(r.ft)}</td>
                    <td className={`${td} text-right`}>{delta(r.ft - r.base)}</td>
                    <td className={`${td} ${CHART_COL}`}>
                      <Dumbbell base={r.base} ft={r.ft} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <DumbbellLegend />
        </Segment>

        <Segment
          title="한국어 쇼핑몰 100문제"
          note="직접 만든 질문과 정답 SQL입니다. v1(Spider만 학습)은 여러 테이블을 이어야 하는 문제에서 무너졌고, 그 약점을 겨냥해 v2를 학습했습니다."
        >
          {[
            { head: "난이도", rows: korean.byLevel.map((r) => ({ k: r.level, ...r })) },
            { head: "정답 SQL의 JOIN 수", rows: korean.byJoins.map((r) => ({ k: r.joins, ...r })) },
          ].map((tbl) => (
            <div key={tbl.head} className="overflow-x-auto [&+&]:mt-6">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className={th}>{tbl.head}</th>
                    <th className={`${th} text-right`}>문제</th>
                    <th className={`${th} text-right`}>베이스라인</th>
                    <th className={`${th} text-right`}>v1</th>
                    <th className={`${th} text-right`}>v2</th>
                  </tr>
                </thead>
                <tbody>
                  {tbl.rows.map((r) => {
                    const p = (v: number) => Math.round((v / r.n) * 100);
                    const worse = (v: number) => p(v) < p(r.base) - 10;
                    return (
                      <tr key={r.k} className={worse(r.ft) || worse(r.ft2) ? "text-thermal" : ""}>
                        <td className={td}>{r.k}</td>
                        <td className={`${td} text-right text-ink-mute`}>{r.n}</td>
                        <td className={`${td} text-right`}>{p(r.base)}%</td>
                        <td className={`${td} text-right ${worse(r.ft) ? UNDERLINE : ""}`}>{p(r.ft)}%</td>
                        <td className={`${td} text-right ${worse(r.ft2) ? UNDERLINE : ""}`}>{p(r.ft2)}%</td>
                      </tr>
                    );
                  })}
                  {tbl.head === "난이도" && (
                    <tr className="font-bold">
                      <td className={`${td} border-t-[1.5px] border-dashed border-ink/50`}>전체</td>
                      <td className={`${td} border-t-[1.5px] border-dashed border-ink/50 text-right text-ink-mute`}>{korean.total}</td>
                      <td className={`${td} border-t-[1.5px] border-dashed border-ink/50 text-right`}>{korean.overall.base}%</td>
                      <td className={`${td} border-t-[1.5px] border-dashed border-ink/50 text-right`}>{korean.overall.ft}%</td>
                      <td className={`${td} border-t-[1.5px] border-dashed border-ink/50 text-right`}>{korean.overall.ft2}%</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          ))}
          <p className="mt-3 text-[12px] text-ink-mute">빨간 밑줄: 베이스라인보다 10%p 넘게 낮음</p>
          <p className="mt-4 text-ink-mute">
            v1은 주문 → 주문상품 → 상품 → 카테고리처럼 긴 경로에서 중간 테이블을 건너뛰었습니다. Spider에서 불필요한 JOIN을
            줄여 준 버릇이 여기서는 독이 된 것으로 봅니다.
          </p>
          <p className="mt-3 text-ink-mute">
            v2는 쇼핑몰과 겹치지 않는 DB 4개({v2Data.dbs.split(" (")[0]})로 만든 한국어 질문 {v2Data.examples}개(그중 JOIN 2개
            이상 {v2Data.multiJoin}개)를 Spider와 섞어 다시 학습했습니다. JOIN 2개 이상 문제는 2개에서 4개로 늘었지만
            베이스라인(9개)에는 크게 못 미쳤고, 어려움 난이도는 그대로입니다. v1 대비 새로 맞음 {korean.flipsV2.fixed}, 새로
            틀림 {korean.flipsV2.broken}으로 우연과 구분되지 않는 차이입니다.
          </p>
        </Segment>

        <Segment
          title="학습 Loss"
          note={`v1: ${training.data} · v2: ${v2Data.mix} · ${training.setup}. v2의 Loss가 낮은 건 규칙적인 템플릿 데이터가 섞여서이고, 실력 차이를 뜻하지 않습니다.`}
        >
          <LossChart />
        </Segment>

        <Segment title="자동수정 실험" note="파인튜닝 모델이 실행 오류를 낸 63문제에 세 방식을 적용했습니다.">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={th}>방식</th>
                  <th className={`${th} text-right`}>정답</th>
                  <th className={`${th} text-right`}>반복</th>
                  <th className={`${th} text-right`}>EX</th>
                </tr>
              </thead>
              <tbody>
                {selfCorrection.map((r, i) => (
                  <tr key={r.label}>
                    <td className={`${td} whitespace-normal ${i === 0 ? UNDERLINE : ""}`}>{r.label}</td>
                    <td className={`${td} text-right`}>{r.fixedRight}</td>
                    <td className={`${td} text-right`}>{r.repeated}</td>
                    <td className={`${td} text-right ${i === 0 ? UNDERLINE : ""}`}>{pct(r.ex)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-ink-mute">
            '반복'은 오류 메시지를 받고도 직전 SQL을 그대로 다시 쓴 횟수입니다. 지시를 더할수록 오히려 반복이 늘어서 가장 단순한
            방식을 기본으로 씁니다.
          </p>
        </Segment>
      </article>
    </div>
  );
}
