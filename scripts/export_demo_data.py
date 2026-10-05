"""데모 화면이 쓰는 실측 데이터를 web/src/data/ 로 내보낸다.

outputs/ 는 커밋되지 않으므로, 화면에 보여 줄 숫자는 이 스크립트로 뽑아 커밋한다.
    python scripts/export_demo_data.py
"""

import json
import re
from pathlib import Path

OUT = Path("web/src/data")


def load_eval(tag: str) -> list[dict]:
    with open(f"outputs/preds_{tag}_eval.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # 한국어 질문 100개 + 두 모델의 채점 결과
    questions = json.loads(Path("data/korean/questions.json").read_text(encoding="utf-8"))
    tags = {"base": "ko-base-3b", "ft": "ko-ft-3b", "ft2": "ko-ft-v2"}
    results = {k: {r["question"]: r["correct"] for r in load_eval(t)}
               for k, t in tags.items() if Path(f"outputs/preds_{t}_eval.jsonl").exists()}
    catalog = [{"id": q["id"], "level": q["level"], "question": q["question"],
                **{k: res[q["question"]] for k, res in results.items()}} for q in questions]
    (OUT / "korean_catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1), encoding="utf-8")

    # 학습 Loss (v1, v2)
    for src, dst in [("loss_table.txt", "loss.json"), ("loss_table_v2.txt", "loss_v2.json")]:
        path = Path("loss_table") / src
        if not path.exists():
            continue
        loss = []
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*(\d+)\s+([0-9.]+)\s*$", line)
            if m:
                loss.append([int(m.group(1)), float(m.group(2))])
        (OUT / dst).write_text(json.dumps(loss), encoding="utf-8")
        print(f"loss {src}: {len(loss)}개")

    print(f"catalog {len(catalog)}문제 ({', '.join(results)}) -> {OUT}")


if __name__ == "__main__":
    main()
