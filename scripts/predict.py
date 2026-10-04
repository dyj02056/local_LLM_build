"""Ollama 모델로 dev 세트 SQL을 생성한다.

사용법:
    python scripts/predict.py --model qwen2.5-coder:3b --limit 200 --tag base-3b
이미 생성된 항목은 건너뛰므로 중단 후 다시 실행해도 이어서 진행된다.
"""

import argparse
import json
import time
from pathlib import Path

from text2sql.llm import chat
from text2sql.prompt import extract_sql


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/sft/dev.jsonl")
    ap.add_argument("--model", default="qwen2.5-coder:3b")
    ap.add_argument("--tag", required=True, help="결과 파일 이름 (예: base-3b, ft-3b)")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    out_path = Path("outputs") / f"preds_{args.tag}.jsonl"
    out_path.parent.mkdir(exist_ok=True)
    done = sum(1 for _ in open(out_path, encoding="utf-8")) if out_path.exists() else 0

    with open(args.data, encoding="utf-8") as f:
        examples = [json.loads(line) for line in f]
    if not examples:
        raise SystemExit(f"{args.data} 가 비어 있습니다. prepare_spider.py 를 먼저 실행하세요.")
    if args.limit:
        examples = examples[: args.limit]

    with open(out_path, "a", encoding="utf-8") as fout:
        for i, ex in enumerate(examples[done:], start=done):
            prompt = ex["messages"][:-1]  # 정답(assistant) 제외
            t0 = time.perf_counter()
            raw = chat(prompt, model=args.model)
            latency = time.perf_counter() - t0
            fout.write(json.dumps({
                "db_id": ex["db_id"],
                "question": ex["question"],
                "gold": ex["query"],
                "pred": extract_sql(raw),
                "raw": raw,
                "latency_s": round(latency, 3),
            }, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"[{i + 1}/{len(examples)}] {latency:.1f}s")


if __name__ == "__main__":
    main()
