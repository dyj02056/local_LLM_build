import type { ModelKey, QueryResult } from "./api";

export type Mode = ModelKey | "compare";

export type Job = {
  id: number;
  no: number; // 영수증 번호
  pairId: number | null; // 비교 모드에서 같은 질문으로 묶인 두 장
  dbId: string;
  modelKey: ModelKey;
  modelName: string;
  question: string;
  selfCorrect: boolean;
  startedAt: number;
  status: "queued" | "printing" | "done" | "failed";
  result?: QueryResult;
  failure?: string;
};

export const MODEL_LABEL: Record<ModelKey, string> = {
  base: "베이스라인",
  ft: "파인튜닝",
};
