export type ModelKey = "base" | "ft" | "ft2";

export type Health = {
  ollama: boolean;
  models: Record<ModelKey, { name: string; installed: boolean }>;
};

export type Database = { id: string; group: "korean" | "spider" };

export type QueryResult = {
  model: string;
  sql: string;
  columns: string[];
  rows: unknown[][];
  truncated: boolean;
  error: string | null;
  attempts: { sql: string; error: string | null }[];
  generation_ms: number;
  execution_ms: number;
};

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* 본문이 JSON이 아니면 상태 코드만 쓴다 */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const getHealth = () => fetch("/api/health").then((r) => asJson<Health>(r));
export const getDatabases = () => fetch("/api/databases").then((r) => asJson<Database[]>(r));

export const runQuery = (body: { db_id: string; question: string; model: ModelKey; self_correct: boolean }) =>
  fetch("/api/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => asJson<QueryResult>(r));
