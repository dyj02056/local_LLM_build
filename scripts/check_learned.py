"""새 모델이 실제로 학습됐는지 확인한다.

새 학습 데이터에만 있는 질문을 새 모델과 이전 모델에 묻고 실행 결과로 채점한다.
Loss가 nan이어도 GGUF는 멀쩡히 만들어지므로, 학습 직후 이 검사로 확인한다.

    python scripts/check_learned.py --new-model text2sql-ft-v3 --old-model text2sql-ft-v2 \
        --new-train data/korean_train/train_ko_v3.jsonl --old-train data/korean_train/train_ko.jsonl
v3 기록: 실패한 1차 학습 v3 22 / v2 26, 정상 학습 v3 30 / v2 27 (30문제, seed 0)
"""

import argparse
import json
import random

from text2sql.evaluate import evaluate_example
from text2sql.llm import chat
from text2sql.prompt import extract_sql


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-model", required=True)
    ap.add_argument("--old-model", required=True)
    ap.add_argument("--new-train", required=True)
    ap.add_argument("--old-train", required=True)
    ap.add_argument("--db-root", default="data/korean_train/database")
    ap.add_argument("-n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    with open(args.old_train, encoding="utf-8") as f:
        seen = {json.loads(line)["question"] for line in f}
    with open(args.new_train, encoding="utf-8") as f:
        new = [ex for ex in map(json.loads, f) if ex["question"] not in seen]
    sample = random.Random(args.seed).sample(new, args.n)
    print(f"새 데이터에만 있는 질문 {len(new)}개 중 {args.n}개")

    for model in [args.new_model, args.old_model]:
        ok = 0
        for ex in sample:
            pred = extract_sql(chat(ex["messages"][:-1], model=model))
            db = f"{args.db_root}/{ex['db_id']}/{ex['db_id']}.sqlite"
            ok += evaluate_example(db, pred, ex["query"]).correct
        print(f"{model}: {ok}/{args.n}")


if __name__ == "__main__":
    main()
