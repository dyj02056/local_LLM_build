"""두 모델의 evaluate.py 결과(_eval.jsonl)를 같은 문제끼리 비교한다.

사용법:
    python scripts/compare.py outputs/preds_base-3b_eval.jsonl outputs/preds_ft-3b_eval.jsonl
    python scripts/compare.py A_eval.jsonl B_eval.jsonl --examples 5 --out outputs/compare.md

B가 아직 다 안 돌았으면 B에 있는 문제 수만큼만 비교한다.
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

CATEGORIES = ["단순 조회", "ORDER BY", "GROUP BY", "JOIN", "집합 연산", "중첩 쿼리"]


def categories(gold: str) -> list[str]:
    """정답 SQL 기준 유형 (한 문제가 여러 유형에 속할 수 있음)."""
    s = gold.lower()
    cats = []
    if re.search(r"\border\s+by\b", s):
        cats.append("ORDER BY")
    if re.search(r"\bgroup\s+by\b", s):
        cats.append("GROUP BY")
    if re.search(r"\bjoin\b", s):
        cats.append("JOIN")
    if re.search(r"\b(union|intersect|except)\b", s):
        cats.append("집합 연산")
    if re.search(r"\(\s*select\b", s):
        cats.append("중첩 쿼리")
    return cats or ["단순 조회"]


def error_kind(r: dict) -> str:
    if r["correct"]:
        return "정답"
    if r["error"] is None:
        return "결과 틀림"
    m = re.match(r"(no such column|no such table|ambiguous column name)", r["error"])
    return f"실행 오류: {m.group(1)}" if m else "실행 오류: 기타"


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def pct(c: int, n: int) -> str:
    return f"{c / n:.1%} ({c}/{n})" if n else "-"


def diff(a: int, b: int, n: int) -> str:
    return f"{(b - a) / n * 100:+.1f}%p" if n else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a", help="기준 (예: 베이스라인) _eval.jsonl")
    ap.add_argument("b", help="비교 대상 (예: 파인튜닝) _eval.jsonl")
    ap.add_argument("--examples", type=int, default=5, help="좋아진/나빠진 사례 출력 개수")
    ap.add_argument("--out", help="마크다운 보고서 저장 경로")
    args = ap.parse_args()

    A, B = load(args.a), load(args.b)
    n = min(len(A), len(B))
    A, B = A[:n], B[:n]
    for i, (a, b) in enumerate(zip(A, B)):
        if a["question"] != b["question"] or a["db_id"] != b["db_id"]:
            raise SystemExit(f"{i}번째 문제가 서로 다릅니다. 같은 dev 순서로 만든 파일인지 확인하세요.")

    na, nb = Path(args.a).stem.removesuffix("_eval"), Path(args.b).stem.removesuffix("_eval")
    lines = [f"# {na} vs {nb} ({n}문제)", ""]

    # 1. 전체
    ca, cb = sum(r["correct"] for r in A), sum(r["correct"] for r in B)
    ea, eb = sum(r["error"] is not None for r in A), sum(r["error"] is not None for r in B)
    lines += ["## 전체", "", f"| 지표 | {na} | {nb} | 변화 |", "|---|---|---|---|"]
    lines.append(f"| 실행 정확도(EX) | {pct(ca, n)} | {pct(cb, n)} | {diff(ca, cb, n)} |")
    lines.append(f"| SQL 오류율 | {pct(ea, n)} | {pct(eb, n)} | {diff(ea, eb, n)} |")
    if "latency_s" in A[0] and "latency_s" in B[0]:
        la, lb = mean(r["latency_s"] for r in A), mean(r["latency_s"] for r in B)
        lines.append(f"| 평균 지연 | {la:.2f}s | {lb:.2f}s | {lb - la:+.2f}s |")
    lines.append("")

    # 2. 오답 유형
    ka, kb = Counter(map(error_kind, A)), Counter(map(error_kind, B))
    kinds = ["결과 틀림"] + sorted(k for k in set(ka) | set(kb) if k.startswith("실행 오류"))
    lines += ["## 오답 내역", "", f"| 구분 | {na} | {nb} | 변화 |", "|---|---|---|---|"]
    for k in kinds:
        lines.append(f"| {k} | {ka[k]} | {kb[k]} | {kb[k] - ka[k]:+d} |")
    lines.append("")

    # 3. SQL 유형별
    by_cat = defaultdict(lambda: [0, 0, 0])  # [문제수, A정답, B정답]
    for a, b in zip(A, B):
        for c in categories(a["gold"]):
            by_cat[c][0] += 1
            by_cat[c][1] += a["correct"]
            by_cat[c][2] += b["correct"]
    lines += ["## SQL 유형별 정답률 (정답 SQL 기준, 중복 포함)", "",
              f"| 유형 | {na} | {nb} | 변화 |", "|---|---|---|---|"]
    for c in CATEGORIES:
        t, x, y = by_cat[c]
        if t:
            lines.append(f"| {c} | {pct(x, t)} | {pct(y, t)} | {diff(x, y, t)} |")
    lines.append("")

    # 4. DB별
    by_db = defaultdict(lambda: [0, 0, 0])
    for a, b in zip(A, B):
        by_db[a["db_id"]][0] += 1
        by_db[a["db_id"]][1] += a["correct"]
        by_db[a["db_id"]][2] += b["correct"]
    lines += ["## DB별 정답률 (변화 큰 순)", "", f"| DB | 문제 수 | {na} | {nb} | 변화 |",
              "|---|---|---|---|---|"]
    for db, (t, x, y) in sorted(by_db.items(), key=lambda kv: (kv[1][1] - kv[1][2]) / kv[1][0]):
        lines.append(f"| {db} | {t} | {x / t:.0%} | {y / t:.0%} | {diff(x, y, t)} |")
    lines.append("")

    # 5. 좋아진 / 나빠진 사례
    fixed = [(a, b) for a, b in zip(A, B) if not a["correct"] and b["correct"]]
    broken = [(a, b) for a, b in zip(A, B) if a["correct"] and not b["correct"]]
    lines += ["## 문제별 변화", "",
              f"- 둘 다 정답: {sum(a['correct'] and b['correct'] for a, b in zip(A, B))}",
              f"- **{na} 오답 → {nb} 정답: {len(fixed)}**",
              f"- **{na} 정답 → {nb} 오답: {len(broken)}**",
              f"- 둘 다 오답: {sum(not a['correct'] and not b['correct'] for a, b in zip(A, B))}", ""]
    for title, pairs in [(f"좋아진 사례 ({na} ✗ → {nb} ✓)", fixed), (f"나빠진 사례 ({na} ✓ → {nb} ✗)", broken)]:
        lines += [f"### {title}", ""]
        for a, b in pairs[: args.examples]:
            lines += [f"- **[{a['db_id']}] {a['question']}**",
                      f"  - 정답: `{a['gold']}`",
                      f"  - {na}: `{a['pred']}`" + (f" — {a['error']}" if a["error"] else ""),
                      f"  - {nb}: `{b['pred']}`" + (f" — {b['error']}" if b["error"] else "")]
        lines.append("")

    report = "\n".join(lines)
    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"보고서 -> {args.out}")


if __name__ == "__main__":
    main()
