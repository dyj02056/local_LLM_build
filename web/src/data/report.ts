// README의 실측 결과. 숫자를 바꿀 때는 README와 함께 바꾼다.

export const spider = {
  total: 1034,
  rows: [
    { label: "베이스라인", ex: 61.8, err: 13.4, lat: 5.52 },
    { label: "베이스라인 + 자동수정", ex: 62.6, err: 10.3, lat: 7.57 },
    { label: "파인튜닝", ex: 73.4, err: 6.1, lat: 5.04 },
    { label: "파인튜닝 + 자동수정", ex: 74.4, err: 3.6, lat: 5.97 },
    { label: "파인튜닝 v2 (+한국어)", ex: 73.1, err: 6.5, lat: 5.34 },
    { label: "파인튜닝 v2 재측정 (v3와 같은 PC)", ex: 71.9, err: 7.0, lat: 5.21 },
    { label: "파인튜닝 v3 (+JOIN 균형)", ex: 72.1, err: 6.6, lat: 5.31 },
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

// base = 베이스라인, ft = 파인튜닝 v1 (Spider), ft2 = 파인튜닝 v2 (Spider + 한국어 다중 JOIN),
// ft3 = 파인튜닝 v3 (Spider + JOIN 수 균형 한국어). 2026-10-07에 네 모델을 같은 컴퓨터에서 다시 잰 값.
export const korean = {
  total: 100,
  overall: { base: 70, ft: 67, ft2: 67, ft3: 67 },
  byLevel: [
    { level: "쉬움", n: 25, base: 24, ft: 24, ft2: 24, ft3: 23 },
    { level: "보통", n: 35, base: 27, ft: 30, ft2: 30, ft3: 29 },
    { level: "어려움", n: 40, base: 19, ft: 13, ft2: 13, ft3: 15 },
  ],
  byJoins: [
    { joins: "0개", n: 58, base: 43, ft: 45, ft2: 44, ft3: 47 },
    { joins: "1개", n: 28, base: 19, ft: 20, ft2: 18, ft3: 16 },
    { joins: "2개 이상", n: 14, base: 8, ft: 2, ft2: 5, ft3: 4 },
  ],
  flips: { fixed: 6, broken: 9, z: -0.8 },
  flipsV2: { fixed: 9, broken: 9, z: 0.0 }, // v1 → v2
  flipsV3: { fixed: 5, broken: 5, z: 0.0 }, // v2 → v3
};

// 외부 LLM 4곳(ChatGPT, Gemini, DeepSeek, Meta)이 쓴 쇼핑몰 질문. 정렬 동점은 --tie-aware로 채점.
// 값은 맞힌 문항 수 (scripts/report_external.py 출력, README 표와 같은 값)
export const external = {
  total: 118,
  overall: { base: 87, ft: 72, ft2: 72, ft3: 82 },
  bySource: [
    { source: "ChatGPT", n: 30, base: 23, ft: 18, ft2: 18, ft3: 22 },
    { source: "Gemini", n: 30, base: 21, ft: 16, ft2: 21, ft3: 20 },
    { source: "DeepSeek", n: 29, base: 27, ft: 21, ft2: 18, ft3: 24 },
    { source: "Meta", n: 29, base: 16, ft: 17, ft2: 15, ft3: 16 },
  ],
  byJoins: [
    { joins: "0개", n: 59, base: 53, ft: 51, ft2: 48, ft3: 53 },
    { joins: "1개", n: 18, base: 17, ft: 14, ft2: 13, ft3: 14 },
    { joins: "2개 이상", n: 41, base: 17, ft: 7, ft2: 11, ft3: 15 },
  ],
  flips: { fixed: 4, broken: 19, z: -3.1 }, // 베이스라인 → v1
  flipsV2Multi: { fixed: 8, broken: 4 }, // v1 → v2, JOIN 2개 이상
  flipsV2Few: { fixed: 3, broken: 7 }, // v1 → v2, JOIN 0~1개
  flipsV3: { fixed: 19, broken: 9, z: 1.9 }, // v2 → v3
  flipsV3Multi: { fixed: 9, broken: 5 }, // v2 → v3, JOIN 2개 이상
  flipsV3Few: { fixed: 10, broken: 4 }, // v2 → v3, JOIN 0~1개
  errRate: { base: 8.5, ft: 21.2, ft2: 25.4, ft3: 14.4 },
};

export const v2Data = {
  dbs: "도서관 · 병원 · 학원 · 여행사 (쇼핑몰과 겹치지 않게 전자상거래 제외)",
  examples: 940,
  multiJoin: 585,
  mix: "Spider 8,659 + 한국어 940 × 2 = 10,539",
};

export const v3Data = {
  examples: 1000,
  split: "JOIN 0개 500 · 1개 150 · 2개 이상 350",
  mix: "Spider 8,659 + 한국어 1,000 × 2 = 10,659",
  where: "Kaggle T4",
};

export const training = {
  data: "Spider train 8,659문제 · 1 epoch",
  setup: "4bit QLoRA · r=16 · lr 2e-4 · Colab T4",
  lossStart: 0.404,
  lossEnd: 0.08,
};
