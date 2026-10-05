export function formatCell(v: unknown): string {
  if (v === null || v === undefined) return "NULL";
  if (typeof v === "number") {
    if (Number.isInteger(v)) return v.toLocaleString("ko-KR");
    return v.toLocaleString("ko-KR", { maximumFractionDigits: 4 });
  }
  return String(v);
}

export const isNumeric = (v: unknown) => typeof v === "number";

export function seconds(ms: number): string {
  return `${(ms / 1000).toFixed(ms < 1000 ? 3 : 2)}초`;
}

export function stamp(ts: number): string {
  const d = new Date(ts);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

/** 두 결과가 같은 행 집합인지 (행 순서 무시) */
export function sameRows(a: unknown[][], b: unknown[][]): boolean {
  if (a.length !== b.length) return false;
  const key = (rows: unknown[][]) => rows.map((r) => JSON.stringify(r)).sort().join("\n");
  return key(a) === key(b);
}
