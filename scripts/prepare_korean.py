"""한국어 질문셋(data/korean/questions.json)을 검증하고 predict.py용 JSONL로 변환한다.

사용법:
    python scripts/build_shop_db.py        # DB 먼저 생성
    python scripts/prepare_korean.py       # -> data/korean/dev_ko.jsonl

검증 항목 (문제가 있으면 경고 출력):
  - 정답 SQL 실행 오류
  - 결과가 비어 있음 (모델이 틀려도 우연히 맞을 수 있음)
  - LIMIT 1인데 1등이 동점 (정답이 모호함)
"""

import argparse
import json
import re
from pathlib import Path

from text2sql.executor import execute
from text2sql.prompt import build_messages
from text2sql.schema import db_path_for, get_schema


def check(db_path: Path, sql: str) -> tuple[list[tuple], list[str]]:
    warnings = []
    _, rows = execute(db_path, sql)
    if not rows or all(v is None for row in rows for v in row):
        warnings.append("결과가 비어 있음")
    if re.search(r"\blimit\s+1\s*$", sql, re.IGNORECASE):
        _, top = execute(db_path, re.sub(r"\blimit\s+1\s*$", "LIMIT 2", sql, flags=re.IGNORECASE))
        # 정렬 기준값은 보통 마지막 컬럼이 아니므로, 행 전체 대신 원래 쿼리의 ORDER BY 식을 다시 계산하기는
        # 어렵다. 대신 LIMIT 2로 두 행을 보고 사람이 확인하도록 보여 준다.
        if len(top) == 2:
            warnings.append(f"LIMIT 1 → 상위 2개 확인 필요: {top}")
    return rows, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default="data/korean/questions.json")
    ap.add_argument("--db-root", default="data/korean/database")
    ap.add_argument("--db-id", default="shop")
    ap.add_argument("--out", default="data/korean/dev_ko.jsonl")
    args = ap.parse_args()

    db_path = db_path_for(args.db_root, args.db_id)
    schema = get_schema(db_path)
    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))

    n_warn = 0
    with open(args.out, "w", encoding="utf-8") as fout:
        for q in questions:
            rows, warnings = check(db_path, q["query"])
            preview = rows[:3] if len(rows) > 3 else rows
            print(f"[{q['id']:>3}] {q['level']} | {q['question']}\n      {len(rows)}행: {preview}")
            for w in warnings:
                print(f"      ⚠ {w}")
            n_warn += bool(warnings)
            fout.write(json.dumps({
                "db_id": args.db_id,
                "question": q["question"],
                "query": q["query"],
                "messages": build_messages(schema, q["question"], q["query"]),
                "id": q["id"],
                "level": q["level"],
            }, ensure_ascii=False) + "\n")
    print(f"\n{len(questions)}문제 -> {args.out} (경고 {n_warn}건)")


if __name__ == "__main__":
    main()
