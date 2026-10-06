"""v2 학습 파일: Spider train + 한국어 다중 JOIN 데이터(반복)를 섞는다.

    python scripts/make_train_v2.py     # -> data/sft/train_v2.jsonl
"""

import argparse
import json
import random
from pathlib import Path


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spider", default="data/sft/train.jsonl")
    ap.add_argument("--korean", default="data/korean_train/train_ko.jsonl")
    ap.add_argument("--korean-repeat", type=int, default=2, help="한국어 데이터 반복 횟수")
    ap.add_argument("--extra", nargs="*", default=[], help="반복 없이 한 번만 섞을 파일 (예: 오류 수정 대화)")
    ap.add_argument("--out", default="data/sft/train_v2.jsonl")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    keep = ("db_id", "question", "query", "messages")
    spider = load(args.spider)
    korean = [{k: r[k] for k in keep} for r in load(args.korean)]
    extra = [{k: r[k] for k in keep} for f in args.extra for r in load(f)]
    rows = spider + korean * args.korean_repeat + extra
    random.Random(args.seed).shuffle(rows)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_ko = len(korean) * args.korean_repeat
    print(f"Spider {len(spider)} + 한국어 {len(korean)}×{args.korean_repeat} = {len(rows)}개 "
          f"(한국어 {n_ko / len(rows):.1%})" + (f" + 추가 {len(extra)}" if extra else "") + f" -> {args.out}")


if __name__ == "__main__":
    main()
