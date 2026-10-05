"""정답 SQL의 최상위 ORDER BY에 동점이 있어 순서(또는 LIMIT 경계)가 하나로 정해지지 않는 문항을 찾는다.

    python scripts/check_order_ties.py data/korean/questions.json [다른 질문 파일 ...]

tie-order: LIMIT 없이 동점끼리 순서만 모호 -> evaluate.py --tie-aware 로 채점하면 공정함
tie-limit: LIMIT 경계에서 동점이 갈려 정답 행 자체가 모호 -> 문항을 고치거나 빼야 함
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from text2sql.ties import tie_variants


def tie_status(db_path, sql: str) -> str | None:
    variants = tie_variants(db_path, sql)
    if variants is None:
        return None
    a, b = variants
    if a == b:
        return "ok"
    return "tie-order" if Counter(a) == Counter(b) else "tie-limit"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--db", default="data/korean/database/shop/shop.sqlite")
    args = ap.parse_args()
    for f in args.files:
        found = []
        for q in json.loads(Path(f).read_text(encoding="utf-8-sig")):
            st = tie_status(args.db, q["query"])
            if st and st != "ok":
                found.append(f"  #{q['id']} {st}: {q['question'][:60]}")
        print(f"{Path(f).name}: 정렬 문항 중 동점 {len(found)}개")
        print("\n".join(found))


if __name__ == "__main__":
    main()
