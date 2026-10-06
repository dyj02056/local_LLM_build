// README의 실측 결과. 숫자를 바꿀 때는 README와 함께 바꾼다.

export const spider = {
  total: 1034,
  rows: [
    { label: "베이스라인", ex: 61.8, err: 13.4, lat: 5.52 },
    { label: "베이스라인 + 자동수정", ex: 62.6, err: 10.3, lat: 7.57 },
    { label: "파인튜닝", ex: 73.4, err: 6.1, lat: 5.04 },
    { label: "파인튜닝 + 자동수정", ex: 74.4, err: 3.6, lat: 5.97 },
    { label: "파인튜닝 v2 (+한국어)", ex: 73.1, err: 6.5, lat: 5.34 },
  ],
  flipsV2: { fixed: 51, broken: 54 }, // v1 → v2
  byType: [
    { type: "단순 조회", n: 333, base: 78.1, ft: 88.3 },
    { type: "ORDER BY", n: 237, base: 62.4, ft: 74.7 },
    { type: "GROUP BY", n: 277, base: 51.6, ft: 66.4 },
    { type: "JOIN", n: 408, base: 51.2, ft: 59.6 },
    { type: "집합 연산", n: 80, base: 43.8, ft: 58.8 },
    { type: "중첩 쿼리", n: 83, base: 37.3, ft: 50.6 },
  ],
  flips: { fixed: 176, broken: 56, z: 7.9 },
};

export const selfCorrection = [
  { label: "오류 메시지만 (기본)", fixedRun: 26, fixedRight: 10, repeated: 25, ex: 74.4, lat: 5.97 },
  { label: "+ 컬럼 목록 힌트", fixedRun: 17, fixedRight: 7, repeated: 38, ex: 74.1, lat: 6.38 },
  { label: "+ 힌트 + 재샘플링", fixedRun: 22, fixedRight: 8, repeated: 31, ex: 74.2, lat: 6.66 },
];

// base = 베이스라인, ft = 파인튜닝 v1 (Spider), ft2 = 파인튜닝 v2 (Spider + 한국어 다중 JOIN)
export const korean = {
  total: 100,
  overall: { base: 71, ft: 66, ft2: 68 },
  byLevel: [
    { level: "쉬움", n: 25, base: 24, ft: 24, ft2: 24 },
    { level: "보통", n: 35, base: 27, ft: 29, ft2: 31 },
    { level: "어려움", n: 40, base: 20, ft: 13, ft2: 13 },
  ],
  byJoins: [
    { joins: "0개", n: 58, base: 43, ft: 45, ft2: 45 },
    { joins: "1개", n: 28, base: 19, ft: 19, ft2: 19 },
    { joins: "2개 이상", n: 14, base: 9, ft: 2, ft2: 4 },
  ],
  flips: { fixed: 6, broken: 11, z: -1.2 },
  flipsV2: { fixed: 8, broken: 6, z: 0.5 }, // v1 → v2
};

// 외부 LLM 4곳(ChatGPT, Gemini, DeepSeek, Meta)이 쓴 쇼핑몰 질문. 정렬 동점은 --tie-aware로 채점.
// 값은 맞힌 문항 수 (scripts/report_external.py 출력, README 표와 같은 값)
export const external = {
  total: 118,
  overall: { base: 87, ft: 72, ft2: 73 },
  bySource: [
    { source: "ChatGPT", n: 30, base: 23, ft: 18, ft2: 18 },
    { source: "Gemini", n: 30, base: 21, ft: 18, ft2: 21 },
    { source: "DeepSeek", n: 29, base: 27, ft: 20, ft2: 20 },
    { source: "Meta", n: 29, base: 16, ft: 16, ft2: 14 },
  ],
  byJoins: [
    { joins: "0개", n: 59, base: 53, ft: 51, ft2: 48 },
    { joins: "1개", n: 18, base: 15, ft: 14, ft2: 11 },
    { joins: "2개 이상", n: 41, base: 19, ft: 7, ft2: 14 },
  ],
  flips: { fixed: 5, broken: 20, z: -3.0 }, // 베이스라인 → v1
  flipsV2Multi: { fixed: 10, broken: 3 }, // v1 → v2, JOIN 2개 이상
  flipsV2Few: { fixed: 3, broken: 9 }, // v1 → v2, JOIN 0~1개
};

export const v2Data = {
  dbs: "도서관 · 병원 · 학원 · 여행사 (쇼핑몰과 겹치지 않게 전자상거래 제외)",
  examples: 940,
  multiJoin: 585,
  mix: "Spider 8,659 + 한국어 940 × 2 = 10,539",
};

export const training = {
  data: "Spider train 8,659문제 · 1 epoch",
  setup: "4bit QLoRA · r=16 · lr 2e-4 · Colab T4",
  lossStart: 0.404,
  lossEnd: 0.08,
};
