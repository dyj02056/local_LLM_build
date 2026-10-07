"""외부 LLM 4곳이 쓴 한국어 질문을 검토 결과대로 정리해 하나의 평가셋으로 만든다.

원본(data/korean/questions_external_<source>.json)은 그대로 두고, 고친 문항과 뺀 문항은 아래에 이유와 함께 기록한다.
질문 생성 프롬프트: data/korean/questions_generation_prompt.md

    python scripts/prepare_external.py
결과: data/korean/questions_external.json (합친 문항), data/korean/dev_ext.jsonl (predict.py 입력)
예시 행 포함: python scripts/prepare_external.py --sample-rows 3 --out data/korean/dev_ext_rows.jsonl
"""

import argparse
import json
from pathlib import Path

from text2sql.prompt import build_messages
from text2sql.schema import db_path_for, get_schema
from text2sql.ties import tie_variants

SOURCES = ["chatgpt", "gemini", "deepseek", "meta"]

# 사람이 검토해 뺀 문항
EXCLUDE = {
    ("deepseek", 30): "정답 결과가 비어 있음 (구매됐지만 리뷰 없는 상품이 DB에 없음)",
    ("meta", 18): "정답이 0명이라 조건을 잘못 쓴 SQL도 우연히 맞힐 수 있음",
}

# 사람이 검토해 고친 문항 (사용자 확인 후 반영)
FIXES = {
    ("chatgpt", 15): {
        "query": "SELECT p.name, avg(r.rating) FROM reviews AS r JOIN products AS p ON r.product_id = p.product_id GROUP BY p.product_id",
        "reason": "'상품별'을 묻는데 정답이 상품 ID만 출력 -> 상품 이름으로 수정",
    },
    ("chatgpt", 16): {
        "query": "SELECT p.name, count(*), avg(r.rating) FROM reviews AS r JOIN products AS p ON r.product_id = p.product_id GROUP BY p.product_id",
        "reason": "'각 상품의'를 묻는데 정답이 상품 ID만 출력 -> 상품 이름으로 수정",
    },
    ("meta", 15): {
        "question_suffix": " 월은 '2025-01'처럼 표시해 줘.",
        "reason": "월 표시 형식이 정해지지 않아 정답이 모호 -> 질문에 형식 명시",
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/korean/dev_ext.jsonl")
    ap.add_argument("--sample-rows", type=int, default=0, help="스키마에 넣을 테이블별 예시 행 수")
    args = ap.parse_args()

    db_path = db_path_for("data/korean/database", "shop")
    schema = get_schema(db_path, args.sample_rows)
    merged, excluded = [], []
    for src in SOURCES:
        for q in json.loads(Path(f"data/korean/questions_external_{src}.json").read_text(encoding="utf-8-sig")):
            key = (src, q["id"])
            if key in EXCLUDE:
                excluded.append(f"{src} #{q['id']}: {EXCLUDE[key]}")
                continue
            question, query, edited = q["question"], q["query"].strip().rstrip(";"), None
            if key in FIXES:
                fix = FIXES[key]
                query = fix.get("query", query)
                question = question + fix.get("question_suffix", "")
                edited = fix["reason"]
            variants = tie_variants(db_path, query)
            merged.append({
                "id": len(merged) + 1, "source": src, "source_id": q["id"], "level": q["level"],
                "question": question, "query": query, "note": q.get("note", ""), "edited": edited,
                "order_ties": bool(variants and variants[0] != variants[1]),
            })

    Path("data/korean/questions_external.json").write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(args.out, "w", encoding="utf-8") as f:
        for q in merged:
            f.write(json.dumps({"db_id": "shop", "question": q["question"], "query": q["query"],
                                "messages": build_messages(schema, q["question"], q["query"]),
                                "id": q["id"], "level": q["level"], "source": q["source"]}, ensure_ascii=False) + "\n")

    print(f"{len(merged)}문항 (제외 {len(excluded)}, 수정 {sum(bool(q['edited']) for q in merged)}, "
          f"정렬 동점 {sum(q['order_ties'] for q in merged)}) -> data/korean/questions_external.json, {args.out}")
    for e in excluded:
        print("  제외:", e)


if __name__ == "__main__":
    main()
