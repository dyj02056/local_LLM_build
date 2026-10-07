"""실행 결과 다수결: 여러 모델이 쓴 SQL을 실행해, 같은 결과를 낸 SQL이 가장 많은 쪽을 고른다.

SQL 문자열이 달라도 결과 행이 같으면(순서 무시) 같은 표로 센다.
실행 오류가 난 SQL은 표가 없다. 동률이면 후보 목록에서 앞에 있는 SQL을 고르므로,
가장 믿는 모델을 맨 앞에 둔다. 모두 실패하면 첫 후보를 그대로 돌려준다.
"""

import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .executor import execute


@dataclass
class VoteResult:
    sql: str
    index: int  # 고른 후보의 위치
    votes: int  # 같은 결과를 낸 후보 수 (0이면 모두 실행 실패)


def result_key(db_path: str | Path, sql: str, timeout_s: float = 5.0) -> frozenset | None:
    """행 순서를 무시한 결과의 지문. 실행 오류면 None."""
    try:
        _, rows = execute(db_path, sql, timeout_s=timeout_s)
    except sqlite3.Error:
        return None
    return frozenset(Counter(map(repr, rows)).items())


def vote(db_path: str | Path, candidates: list[str], timeout_s: float = 5.0) -> VoteResult:
    if not candidates:
        raise ValueError("후보 SQL이 없습니다")
    keys = [result_key(db_path, sql, timeout_s) for sql in candidates]
    counts = Counter(k for k in keys if k is not None)
    if not counts:
        return VoteResult(candidates[0], 0, 0)
    top = max(counts.values())
    index = next(i for i, k in enumerate(keys) if k is not None and counts[k] == top)
    return VoteResult(candidates[index], index, top)
