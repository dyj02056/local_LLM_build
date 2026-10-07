import type { ReactNode } from "react";
import { external, korean, noTrain, selfCorrection, spider, training, v2Data, v3Data } from "../data/report";
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
const tdTotal = `${td} border-t-[1.5px] border-dashed border-ink/50`;

type ModelCounts = { k: string; n: number; base: number; ft: number; ft2: number; ft3: number };

/** 베이스라인 · v1 · v2 · v3 정답률 표. 값은 맞힌 문항 수, 표시는 %. total이 있으면 합계 줄을 붙인다. */
function ModelTable({ head, rows, total }: { head: string; rows: ModelCounts[]; total?: ModelCounts }) {
  const p = (v: number, n: number) => Math.round((v / n) * 100);
  const totalPct = (v: number) => (total!.n === 100 ? `${v}%` : pct((v / total!.n) * 100));
  return (
    <div className="overflow-x-auto [&+&]:mt-6">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className={th.replace("whitespace-nowrap", "break-keep")}>{head}</th>
            <th className={`${th} text-right`}>문제</th>
            <th className={`${th} text-right`}>베이스라인</th>
            <th className={`${th} text-right`}>v1</th>
            <th className={`${th} text-right`}>v2</th>
            <th className={`${th} text-right`}>v3</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const worse = (v: number) => p(v, r.n) < p(r.base, r.n) - 10;
            return (
              <tr key={r.k} className={worse(r.ft) || worse(r.ft2) || worse(r.ft3) ? "text-thermal" : ""}>
                <td className={td}>{r.k}</td>
                <td className={`${td} text-right text-ink-mute`}>{r.n}</td>
                <td className={`${td} text-right`}>{p(r.base, r.n)}%</td>
                <td className={`${td} text-right ${worse(r.ft) ? UNDERLINE : ""}`}>{p(r.ft, r.n)}%</td>
                <td className={`${td} text-right ${worse(r.ft2) ? UNDERLINE : ""}`}>{p(r.ft2, r.n)}%</td>
                <td className={`${td} text-right ${worse(r.ft3) ? UNDERLINE : ""}`}>{p(r.ft3, r.n)}%</td>
              </tr>
            );
          })}
          {total && (
            <tr className="font-bold">
              <td className={tdTotal}>{total.k}</td>
              <td className={`${tdTotal} text-right text-ink-mute`}>{total.n}</td>
              <td className={`${tdTotal} text-right`}>{totalPct(total.base)}</td>
              <td className={`${tdTotal} text-right`}>{totalPct(total.ft)}</td>
              <td className={`${tdTotal} text-right`}>{totalPct(total.ft2)}</td>
              <td className={`${tdTotal} text-right`}>{totalPct(total.ft3)}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function ZTape() {
  const s0 = spider.rows[0];
  const s2 = spider.rows[2];
  const ext = {
    base: (external.overall.base / external.total) * 100,
    ft: (external.overall.ft / external.total) * 100,
    ft2: (external.overall.ft2 / external.total) * 100,
    ft3: (external.overall.ft3 / external.total) * 100,
  };
  const [j0, j1, j2] = external.byJoins;
  const extMulti = { base: `${j2.base}/${j2.n}`, ft: `${j2.ft}/${j2.n}`, ft2: `${j2.ft2}/${j2.n}`, ft3: `${j2.ft3}/${j2.n}` };
  const few = j0.n + j1.n;
  const extFew = {
    base: `${j0.base + j1.base}/${few}`,
    ft: `${j0.ft + j1.ft}/${few}`,
    ft2: `${j0.ft2 + j1.ft2}/${few}`,
    ft3: `${j0.ft3 + j1.ft3}/${few}`,
  };
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
      <p className="text-ink-mute">v2: 한국어 다중 JOIN 940문제 · v3: JOIN 수 균형 1,000문제</p>
      {line("한국어 정확도 (v1→v2→v3)", `${korean.overall.ft}% → ${korean.overall.ft2}% → ${korean.overall.ft3}%`)}
      {line("JOIN 2개 이상", `${korean.byJoins[2].ft}/14 → ${korean.byJoins[2].ft2}/14 → ${korean.byJoins[2].ft3}/14`)}
      {line("Spider (v1→v2)", `${pct(s2.ex)} → ${pct(spider.rows[4].ex)}`)}
      {line("Spider (v2→v3, 같은 PC)", `${pct(spider.rows[5].ex)} → ${pct(spider.rows[6].ex)}`)}
      <div className="rule-dash my-3" />
      <p className="text-ink-mute">외부 AI 질문 {external.total}문항 (베이스→v1→v2→v3)</p>
      {line("실행 정확도", [ext.base, ext.ft, ext.ft2, ext.ft3].map((v) => `${Math.round(v)}%`).join(" → "))}
      {line("JOIN 2개 이상", `${extMulti.base} → ${extMulti.ft} → ${extMulti.ft2} → ${extMulti.ft3}`)}
      {line("JOIN 0~1개", `${extFew.base} → ${extFew.ft} → ${extFew.ft2} → ${extFew.ft3}`)}
      <div className="rule-double my-3" />
      <div className="leader font-bold">
        <span className="dh">v3 효과 (v2 대비)</span>
        <span className="dh">{delta(ext.ft3 - ext.ft2)}</span>
      </div>
      <div className="rule-dash my-3" />
      <p className="text-ink-mute">학습 없이 올리기 (외부 질문 {external.total}문항)</p>
      {line("7B 베이스라인", `${Math.round((noTrain.rows[2].ext / external.total) * 100)}%`)}
      {line("3B 다수결 5개", `${Math.round((noTrain.rows[4].ext / external.total) * 100)}%`)}
      {line("Spider v3 → 다수결 5개", `${pct(noTrain.rows[1].spider!)} → ${pct(noTrain.rows[4].spider!)}`)}
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
          note="직접 만든 질문과 정답 SQL입니다. v1(Spider만 학습)은 여러 테이블을 이어야 하는 문제에서 무너졌고, 그 약점을 겨냥해 v2와 v3를 학습했습니다."
        >
          <ModelTable
            head="난이도"
            rows={korean.byLevel.map((r) => ({ k: r.level, ...r }))}
            total={{ k: "전체", n: korean.total, ...korean.overall }}
          />
          <ModelTable head="정답 SQL의 JOIN 수" rows={korean.byJoins.map((r) => ({ k: r.joins, ...r }))} />
          <p className="mt-3 text-[12px] text-ink-mute">빨간 밑줄: 베이스라인보다 10%p 넘게 낮음</p>
          <p className="mt-4 text-ink-mute">
            v1은 주문 → 주문상품 → 상품 → 카테고리처럼 긴 경로에서 중간 테이블을 건너뛰었습니다. Spider에서 불필요한 JOIN을
            줄여 준 버릇이 여기서는 독이 된 것으로 봅니다.
          </p>
          <p className="mt-3 text-ink-mute">
            v2는 쇼핑몰과 겹치지 않는 DB 4개({v2Data.dbs.split(" (")[0]})로 만든 한국어 질문 {v2Data.examples}개(그중 JOIN 2개
            이상 {v2Data.multiJoin}개)를 Spider와 섞어 다시 학습했습니다. JOIN 2개 이상 문제는 {korean.byJoins[2].ft}개에서{" "}
            {korean.byJoins[2].ft2}개로 늘었지만 베이스라인({korean.byJoins[2].base}개)에는 못 미쳤고, 어려움 난이도는 그대로입니다. v1 대비 새로 맞음 {korean.flipsV2.fixed}, 새로
            틀림 {korean.flipsV2.broken}개로 우연과 구분되지 않는 차이입니다.
          </p>
          <p className="mt-3 text-ink-mute">
            v3는 JOIN이 필요 없는 질문까지 균형 있게 섞어 학습했지만, 이 100문제에서는 v2 대비 새로 맞음 {korean.flipsV3.fixed}, 새로
            틀림 {korean.flipsV3.broken}개로 차이가 없었습니다. 차이는 외부 질문에서 드러났습니다 (아래).
          </p>
          <p className="mt-3 text-[12px] text-ink-mute">
            2026-10-07에 네 모델을 같은 컴퓨터에서 다시 쟀습니다. 처음 측정과 1~3문제씩 다를 수 있습니다.
          </p>
        </Segment>

        <Segment
          title="외부 AI 질문 118문항"
          note="같은 사람이 만든 질문만으로 평가하면 말투 덕을 볼 수 있어서, ChatGPT · Gemini · DeepSeek · Meta가 같은 쇼핑몰 DB로 쓴 질문과 정답 SQL로 다시 채점했습니다. 정렬 동점이 있는 문항은 동점끼리 순서를 바꿔도 정답으로 봅니다."
        >
          <ModelTable
            head="정답 SQL의 JOIN 수"
            rows={external.byJoins.map((r) => ({ k: r.joins, ...r }))}
            total={{ k: "전체", n: external.total, ...external.overall }}
          />
          <ModelTable head="질문을 쓴 AI" rows={external.bySource.map((r) => ({ k: r.source, ...r }))} />
          <p className="mt-3 text-[12px] text-ink-mute">빨간 밑줄: 베이스라인보다 10%p 넘게 낮음</p>
          <p className="mt-4 text-ink-mute">
            말투 이점은 없었습니다. 베이스라인 대비 v1의 하락은 직접 만든 질문({korean.overall.ft - korean.overall.base}%p)보다 외부 질문(
            {delta(((external.overall.ft - external.overall.base) / external.total) * 100)})에서 더 컸습니다 (새로 맞음 {external.flips.fixed}, 새로 틀림 {external.flips.broken}, z ≈ {external.flips.z.toFixed(1)}).
          </p>
          <p className="mt-3">
            <span className={UNDERLINE}>v1은 테이블을 너무 적게 잇고, v2는 너무 많이 잇습니다.</span>{" "}
            <span className="text-ink-mute">
              v1과 비교하면 v2는 JOIN 2개 이상 문항에서 좋아졌지만(새로 맞음 {external.flipsV2Multi.fixed}, 새로 틀림{" "}
              {external.flipsV2Multi.broken}), JOIN 0~1개 문항에서는 나빠졌습니다(새로 맞음 {external.flipsV2Few.fixed}, 새로
              틀림 {external.flipsV2Few.broken}). 예를 들어 "브랜드별 상품 수"는 products만 쓰면 되는데
              categories를 붙이고 거기서 brand를 찾다가 실행 오류가 났습니다.
            </span>
          </p>
          <p className="mt-3">
            <span className={UNDERLINE}>v3는 둘 사이의 균형을 잡았습니다.</span>{" "}
            <span className="text-ink-mute">
              JOIN 수를 {v3Data.split} 비율로 맞춘 한국어 {v3Data.examples.toLocaleString()}개로 다시 학습했습니다. v2와 비교하면 JOIN
              0~1개(새로 맞음 {external.flipsV3Few.fixed}, 새로 틀림 {external.flipsV3Few.broken})와 2개 이상(새로 맞음{" "}
              {external.flipsV3Multi.fixed}, 새로 틀림 {external.flipsV3Multi.broken})이 함께 좋아졌고, SQL 오류율은{" "}
              {external.errRate.ft2}%에서 {external.errRate.ft3}%로 줄었습니다. 다만 베이스라인에는 아직 못 미칩니다.
            </span>
          </p>
        </Segment>

        <Segment
          title="학습 없이 올리기: 7B와 다수결"
          note="학습을 더 하지 않고 모델 크기(3B → 7B)나 여러 답의 다수결로 정확도를 올릴 수 있는지 쟀습니다. 다수결은 모델마다 SQL을 쓰게 한 뒤 실행해서, 결과 행이 같은 SQL이 가장 많은 쪽을 고릅니다."
        >
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={th}>방식</th>
                  <th className={`${th} text-right`}>Spider</th>
                  <th className={`${th} text-right`}>한국어 100</th>
                  <th className={`${th} text-right`}>외부 118</th>
                </tr>
              </thead>
              <tbody>
                {noTrain.rows.map((r) => {
                  const bestSpider = Math.max(...noTrain.rows.map((x) => x.spider ?? 0));
                  const bestKo = Math.max(...noTrain.rows.map((x) => x.ko));
                  const bestExt = Math.max(...noTrain.rows.map((x) => x.ext));
                  return (
                    <tr key={r.label}>
                      <td className={`${td} whitespace-normal`}>{r.label}</td>
                      <td className={`${td} text-right ${r.spider === bestSpider ? UNDERLINE : ""} ${r.spider === null ? "text-ink-mute" : ""}`}>
                        {r.spider === null ? "측정 안 함" : pct(r.spider)}
                      </td>
                      <td className={`${td} text-right ${r.ko === bestKo ? UNDERLINE : ""}`}>{r.ko}%</td>
                      <td className={`${td} text-right ${r.ext === bestExt ? UNDERLINE : ""}`}>
                        {pct((r.ext / external.total) * 100)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[12px] text-ink-mute">
            Spider 숫자는 v3만 이번에 새로 재고 나머지는 처음 컴퓨터 값이라 환경이 섞여 있습니다. 한국어 100문제와 외부 118문항의 7B ·
            다수결 값은 다른 컴퓨터에서 쟀습니다. 1%p 안팎은 실력 차이로 보지 않습니다.
          </p>

          <p className="mt-5">
            <span className={UNDERLINE}>한국어에서는 모델 크기가 학습을 이겼습니다.</span>{" "}
            <span className="text-ink-mute">
              7B 베이스라인은 외부 질문 {pct((noTrain.rows[2].ext / external.total) * 100)}로, 3B 베이스라인({pct((noTrain.rows[0].ext / external.total) * 100)})과 가장 잘
              학습한 v3({pct((noTrain.rows[1].ext / external.total) * 100)})를 앞섭니다. 특히 JOIN 2개 이상 문항에서 {noTrain.sevenB.byJoins[2].b7}/
              {noTrain.sevenB.byJoins[2].n}로 3B 베이스라인({noTrain.sevenB.byJoins[2].base}/{noTrain.sevenB.byJoins[2].n})의 거의 두 배이고, SQL 오류율은{" "}
              {noTrain.sevenB.errRate.base}%에서 {noTrain.sevenB.errRate.b7}%로 줄었습니다. 대신 응답이 {noTrain.sevenB.lat.base}초에서{" "}
              {noTrain.sevenB.lat.b7}초로 늘었습니다. JOIN 1개 문항만 17개에서 15개로 줄었습니다.
            </span>
          </p>

          <p className="mt-6 mb-2 font-bold">Spider 5개 다수결: 고른 SQL을 몇 후보가 지지했나</p>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={th}>같은 결과를 낸 후보</th>
                  <th className={`${th} text-right`}>문제</th>
                  <th className={`${th} text-right`}>다수결 정답</th>
                  <th className={`${th} text-right`}>v3 혼자 정답</th>
                </tr>
              </thead>
              <tbody>
                {noTrain.voteBuckets.map((b) => (
                  <tr key={b.votes} className={b.vote > b.v3 ? "" : b.vote < b.v3 ? "text-thermal" : ""}>
                    <td className={td}>{b.votes === 0 ? "0표 (모두 실행 오류)" : `${b.votes}표`}</td>
                    <td className={`${td} text-right text-ink-mute`}>{b.n}</td>
                    <td className={`${td} text-right ${b.vote > b.v3 ? UNDERLINE : ""}`}>{b.vote}</td>
                    <td className={`${td} text-right`}>{b.v3}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[12px] text-ink-mute">밑줄: 다수결이 v3 혼자보다 많이 맞힘 · 빨강: 적게 맞힘</p>

          <p className="mt-5">
            <span className={UNDERLINE}>같은 모델의 변형을 섞으면 손해, 서로 다른 모델을 섞으면 이득이었습니다.</span>{" "}
            <span className="text-ink-mute">
              베이스라인 · v3 · 베이스라인 + 예시 행 3개 다수결은 v3 혼자({pct(noTrain.rows[1].spider!)})보다 낮은 {pct(noTrain.rows[3].spider!)}였습니다 (새로 맞음{" "}
              {noTrain.flips3.fixed}, 새로 틀림 {noTrain.flips3.broken}). 베이스라인과 예시 행은 같은 모델이라 답이 비슷하고, 2표 싸움에서 둘이 한 편이 되어 더 강한 v3를
              이겼기 때문입니다. v2 · v1을 더한 5개 다수결은 {pct(noTrain.rows[4].spider!)}로 v3보다 높고, 새로 맞음 {noTrain.flips5.fixed}, 새로 틀림{" "}
              {noTrain.flips5.broken}(z ≈ {noTrain.flips5.z})입니다. 5개 중 하나라도 맞힌 문제는 {noTrain.oracle5}%라서 답을 고르는 방식을 더 다듬을 여지는 남아 있습니다.
            </span>
          </p>
          <p className="mt-3 text-ink-mute">
            대가는 시간입니다. 모델을 여러 번 돌리므로 평균 응답이 {noTrain.lat.v3}초(v3)에서 {noTrain.lat.vote3}초(3개), {noTrain.lat.vote5}초(5개)로 늘고, SQL 오류율은{" "}
            {noTrain.err.v3}%에서 {noTrain.err.vote5}%로 줄었습니다. 후보 조합과 동률 우선순위는 Spider 결과를 보기 전에 정했습니다. 계산대의 '다수결' 모드가 이 조합을 그대로
            씁니다.
          </p>
        </Segment>

        <Segment
          title="학습 Loss"
          note={`v1: ${training.data} · v2: ${v2Data.mix} · v3: ${v3Data.mix} (${v3Data.where}) · ${training.setup}. v2·v3의 Loss가 낮은 건 규칙적인 템플릿 데이터가 섞여서이고, 실력 차이를 뜻하지 않습니다.`}
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
