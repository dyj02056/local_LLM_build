"""predict.py 결과의 실행 정확도를 계산한다.

사용법:
    python scripts/evaluate.py outputs/preds_base-3b.jsonl
"""

import argparse
import json
from pathlib import Path
from statistics import mean

from text2sql.evaluate import evaluate_example
from text2sql.schema import db_path_for


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("preds")
    ap.add_argument("--db-root", default="data/spider/database")
    ap.add_argument("--tie-aware", action="store_true",
                    help="정답 정렬에 동점이 있으면 동점끼리의 순서 차이는 정답으로 인정 (외부 질문셋용)")
    args = ap.parse_args()

    with open(args.preds, encoding="utf-8") as f:
        preds = [json.loads(line) for line in f]
    if not preds:
        raise SystemExit(f"{args.preds} 가 비어 있습니다. predict.py 가 정상적으로 끝났는지 확인하세요.")

    results = []
    for p in preds:
        r = evaluate_example(db_path_for(args.db_root, p["db_id"]), p["pred"], p["gold"], tie_aware=args.tie_aware)
        results.append({**p, "correct": r.correct, "error": r.error})

    n = len(results)
    correct = sum(r["correct"] for r in results)
    errors = sum(r["error"] is not None for r in results)
    print(f"examples        : {n}")
    print(f"execution acc   : {correct / n:.1%} ({correct}/{n})")
    print(f"sql error rate  : {errors / n:.1%}")
    if "latency_s" in results[0]:
        print(f"avg latency     : {mean(r['latency_s'] for r in results):.2f}s")

    out = Path(args.preds).with_name(Path(args.preds).stem + "_eval.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"상세 결과 -> {out}")


if __name__ == "__main__":
    main()
