"""여러 모델의 예측 파일을 실행 결과 다수결로 합쳐 새 예측 파일을 만든다.

각 모델은 temperature 0이라 따로 돌린 예측을 나중에 합쳐도 실시간 다수결과 결과가 같다.
앞에 둔 모델일수록 동률에서 우선한다.

    python scripts/vote.py --tag ext-vote3 --db-root data/korean/database \
        outputs/preds_ext-base-3b.jsonl outputs/preds_ext-ft-v3.jsonl outputs/preds_ext-base-3b-rows.jsonl
    python scripts/evaluate.py outputs/preds_ext-vote3.jsonl --db-root data/korean/database --tie-aware
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from text2sql.schema import db_path_for
from text2sql.vote import vote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("preds", nargs="+", help="predict.py 결과 파일 (우선순위 순서)")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--db-root", default="data/spider/database")
    args = ap.parse_args()

    runs = []
    for path in args.preds:
        with open(path, encoding="utf-8") as f:
            runs.append([json.loads(line) for line in f])
    n = len(runs[0])
    if any(len(r) != n for r in runs):
        raise SystemExit("예측 파일의 문제 수가 다릅니다: " + ", ".join(str(len(r)) for r in runs))
    for i in range(n):
        if len({r[i]["question"] for r in runs}) != 1:
            raise SystemExit(f"{i + 1}번째 줄의 질문이 파일마다 다릅니다")

    out = Path("outputs") / f"preds_{args.tag}.jsonl"
    picked = Counter()
    with open(out, "w", encoding="utf-8") as f:
        for i in range(n):
            ex = runs[0][i]
            r = vote(db_path_for(args.db_root, ex["db_id"]), [run[i]["pred"] for run in runs])
            picked[r.index] += 1
            f.write(json.dumps({
                "db_id": ex["db_id"], "question": ex["question"], "gold": ex["gold"], "pred": r.sql,
                "picked": Path(args.preds[r.index]).stem.removeprefix("preds_"), "votes": r.votes,
                "latency_s": round(sum(run[i]["latency_s"] for run in runs), 3),
            }, ensure_ascii=False) + "\n")
    print(f"{n}문제 -> {out}")
    for idx, c in sorted(picked.items()):
        print(f"  {Path(args.preds[idx]).name}: {c}번 선택")


if __name__ == "__main__":
    main()
