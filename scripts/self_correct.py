"""predict.py 결과 중 실행 오류가 난 SQL만 self-correction으로 다시 고친다.

사용법:
    python scripts/self_correct.py --model text2sql-ft --src ft-3b --tag ft-3b-sc
결과는 outputs/preds_<tag>.jsonl (predict.py와 같은 형식)이라 evaluate.py / compare.py에 그대로 넣을 수 있다.
실행 오류가 없는 문제는 모델을 부르지 않고 그대로 복사한다. 중단 후 다시 실행하면 이어서 진행된다.
"""

import argparse
import json
import time
from functools import partial
from pathlib import Path

from text2sql.correct import self_correct
from text2sql.llm import chat
from text2sql.schema import db_path_for


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--src", required=True, help="고칠 대상 predict 결과 태그 (예: ft-3b)")
    ap.add_argument("--tag", required=True, help="결과 태그 (예: ft-3b-sc)")
    ap.add_argument("--rounds", type=int, default=2, help="문제당 최대 재시도 횟수")
    ap.add_argument("--hint", action="store_true", help="오류 메시지와 함께 테이블별 실제 컬럼 목록을 준다")
    ap.add_argument("--repeat-temp", type=float, default=None,
                    help="이미 시도한 SQL이 또 나오면 이 temperature로 다시 샘플링 (예: 0.7)")
    ap.add_argument("--data", default="data/sft/dev.jsonl")
    ap.add_argument("--db-root", default="data/spider/database")
    args = ap.parse_args()

    with open(Path("outputs") / f"preds_{args.src}.jsonl", encoding="utf-8") as f:
        preds = [json.loads(line) for line in f]
    with open(args.data, encoding="utf-8") as f:
        examples = [json.loads(line) for line in f][: len(preds)]

    out_path = Path("outputs") / f"preds_{args.tag}.jsonl"
    done = sum(1 for _ in open(out_path, encoding="utf-8")) if out_path.exists() else 0
    chat_fn = partial(chat, model=args.model)

    with open(out_path, "a", encoding="utf-8") as fout:
        for i in range(done, len(preds)):
            p, ex = preds[i], examples[i]
            if p["question"] != ex["question"]:
                raise SystemExit(f"{i}번째 문제가 dev 데이터와 다릅니다.")
            t0 = time.perf_counter()
            sql, history = self_correct(
                ex["messages"][:-1], p["pred"], db_path_for(args.db_root, p["db_id"]), chat_fn, args.rounds,
                use_hint=args.hint, repeat_temperature=args.repeat_temp,
            )
            extra = time.perf_counter() - t0
            row = {**p, "pred": sql, "latency_s": round(p["latency_s"] + extra, 3),
                   "pred_before_sc": p["pred"], "sc_rounds": len(history), "sc_history": history}
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            fout.flush()
            if history:
                status = "OK" if history[-1]["error"] is None else "still error"
                print(f"[{i + 1}/{len(preds)}] {len(history)} round(s), {extra:.1f}s -> {status}")


if __name__ == "__main__":
    main()
