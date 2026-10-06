"""외부 LLM 질문셋 결과를 모델 × (출처, 난이도, JOIN 수)로 정리하고, 직접 만든 100문제 결과와 나란히 비교한다.

    python scripts/report_external.py
입력: outputs/preds_ext-*_eval.jsonl, outputs/preds_ko-*_eval.jsonl (evaluate.py 결과)
"""

import json
import math
import re
from collections import defaultdict
from pathlib import Path

MODELS = {"base": "베이스라인", "ft": "파인튜닝 v1", "ft2": "파인튜닝 v2", "ft3": "파인튜닝 v3"}
EXT = {"base": "ext-base-3b", "ft": "ext-ft-3b", "ft2": "ext-ft-v2", "ft3": "ext-ft-v3"}
OWN = {"base": "ko-base-3b", "ft": "ko-ft-3b", "ft2": "ko-ft-v2", "ft3": "ko-ft-v3"}
SOURCE_NAME = {"chatgpt": "ChatGPT", "gemini": "Gemini", "deepseek": "DeepSeek", "meta": "Meta"}


def load(tag):
    with open(f"outputs/preds_{tag}_eval.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def joins(sql):
    j = len(re.findall(r"\bJOIN\b", sql, re.I))
    return "0개" if j == 0 else "1개" if j == 1 else "2개 이상"


def table(title, groups, results):
    """groups: {그룹 이름: [문항 인덱스]}"""
    lines = [f"### {title}", "", "| 구분 | 문항 | " + " | ".join(MODELS.values()) + " |",
             "|---|---|" + "---|" * len(MODELS)]
    for name, idx in groups.items():
        cells = []
        for k in MODELS:
            c = sum(results[k][i]["correct"] for i in idx)
            cells.append(f"{c / len(idx):.0%} ({c})")
        lines.append(f"| {name} | {len(idx)} | " + " | ".join(cells) + " |")
    return lines + [""]


def flips(a, b):
    up = sum(not x["correct"] and y["correct"] for x, y in zip(a, b))
    down = sum(x["correct"] and not y["correct"] for x, y in zip(a, b))
    z = (up - down) / math.sqrt(up + down) if up + down else 0.0
    return up, down, z


def main():
    qs = json.loads(Path("data/korean/questions_external.json").read_text(encoding="utf-8"))
    ext = {k: load(t) for k, t in EXT.items()}
    own = {k: load(t) for k, t in OWN.items()}
    n = len(qs)

    out = [f"# 외부 LLM 질문셋 평가 ({n}문항)", ""]
    lines = ["### 질문 출처별 비교", "", "| 질문셋 | 문항 | " + " | ".join(MODELS.values()) + " |",
             "|---|---|" + "---|" * len(MODELS)]
    for name, res, size in [("직접 만든 질문", own, 100), ("외부 LLM 질문 (합계)", ext, n)]:
        cells = [f"{sum(r['correct'] for r in res[k]) / size:.1%}" for k in MODELS]
        lines.append(f"| {name} | {size} | " + " | ".join(cells) + " |")
    out += lines + [""]

    by_src = defaultdict(list)
    by_level = defaultdict(list)
    by_join = defaultdict(list)
    for i, q in enumerate(qs):
        by_src[SOURCE_NAME[q["source"]]].append(i)
        by_level[q["level"]].append(i)
        by_join[joins(q["query"])].append(i)
    out += table("외부 질문: 출처(LLM)별", dict(by_src), ext)
    out += table("외부 질문: 난이도별 (각 LLM이 매긴 난이도)", {k: by_level[k] for k in ["쉬움", "보통", "어려움"]}, ext)
    out += table("외부 질문: 정답 SQL의 JOIN 수별", {k: by_join[k] for k in ["0개", "1개", "2개 이상"] if by_join[k]}, ext)

    out += ["### 문제별 변화 (외부 질문)", ""]
    for a, b in [("base", "ft"), ("ft", "ft2"), ("base", "ft2"), ("ft2", "ft3"), ("ft", "ft3"), ("base", "ft3")]:
        up, down, z = flips(ext[a], ext[b])
        out.append(f"- {MODELS[a]} → {MODELS[b]}: 새로 맞음 {up}, 새로 틀림 {down}, 부호 검정 z ≈ {z:.1f}")
    out.append("")

    report = "\n".join(out)
    Path("outputs/report_external.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
