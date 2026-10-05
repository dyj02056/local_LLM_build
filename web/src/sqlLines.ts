const CLAUSE =
  /\b(FROM|(?:(?:LEFT|RIGHT|INNER|OUTER|CROSS|FULL)\s+)*JOIN|WHERE|GROUP\s+BY|HAVING|ORDER\s+BY|LIMIT|UNION(?:\s+ALL)?|INTERSECT|EXCEPT)\b/iy;

/**
 * SQL을 절 단위 줄로 나눈다 (POS가 품목을 한 줄씩 찍듯).
 * 괄호 안(서브쿼리)과 따옴표 안은 나누지 않는다.
 */
export function sqlLines(sql: string): string[] {
  const s = sql.replace(/\s+/g, " ").trim();
  const lines: string[] = [];
  let depth = 0;
  let quote: string | null = null;
  let start = 0;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (quote) {
      if (c === quote) quote = null;
      continue;
    }
    if (c === "'" || c === '"') quote = c;
    else if (c === "(") depth++;
    else if (c === ")") depth--;
    else if (depth === 0 && i > start && (i === 0 || /\s/.test(s[i - 1]))) {
      CLAUSE.lastIndex = i;
      if (CLAUSE.test(s)) {
        lines.push(s.slice(start, i).trim());
        start = i;
      }
    }
  }
  lines.push(s.slice(start).trim());
  return lines.filter(Boolean);
}
