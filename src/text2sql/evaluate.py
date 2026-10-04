"""실행 정확도(Execution Accuracy, EX).

SQL 문자열이 달라도 같은 결과를 내면 정답으로 본다.
  - 정답 SQL에 ORDER BY가 있으면 행 순서까지 비교
  - 없으면 행을 멀티셋으로 비교 (순서 무시, 중복 개수는 반영)
"""

import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .executor import execute


def results_match(pred_rows: list[tuple], gold_rows: list[tuple], ordered: bool) -> bool:
    if ordered:
        return pred_rows == gold_rows
    return Counter(pred_rows) == Counter(gold_rows)


@dataclass
class ExampleResult:
    correct: bool
    error: str | None = None


def evaluate_example(db_path: str | Path, pred_sql: str, gold_sql: str, timeout_s: float = 10.0) -> ExampleResult:
    try:
        _, gold_rows = execute(db_path, gold_sql, timeout_s=timeout_s)
    except sqlite3.Error as e:
        return ExampleResult(False, f"gold failed: {e}")
    try:
        _, pred_rows = execute(db_path, pred_sql, timeout_s=timeout_s)
    except sqlite3.Error as e:
        return ExampleResult(False, str(e))
    ordered = "order by" in gold_sql.lower()
    return ExampleResult(results_match(pred_rows, gold_rows, ordered))
