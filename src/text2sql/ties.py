"""정답 SQL의 정렬에 동점이 있을 때 '동점끼리는 순서를 바꿔도 정답'으로 채점하기 위한 도구.

정답 SQL의 최상위 ORDER BY 뒤에 결과 컬럼 전체를 동점 처리 기준으로 붙여 오름차순·내림차순 두 번 실행한다.
두 결과가 다르면 동점이 있다는 뜻이고, 두 결과의 앞부분(prefix)이 같은 행 집합이 되는 지점이 동점 묶음의 경계다.
"""

import re
import sqlite3
from collections import Counter
from pathlib import Path

from .executor import execute


def top_level_order_by(sql: str) -> tuple[int | None, int | None]:
    """괄호·따옴표 밖(최상위)에 있는 마지막 ORDER BY 위치와 LIMIT 위치."""
    depth, quote, order_at, limit_at = 0, None, None, None
    for i, ch in enumerate(sql):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and (i == 0 or not (sql[i - 1].isalnum() or sql[i - 1] == "_")):
            if re.match(r"ORDER\s+BY\b", sql[i:], re.I):
                order_at = i
            elif re.match(r"LIMIT\b", sql[i:], re.I):
                limit_at = i
    return order_at, limit_at


def tie_variants(db_path: str | Path, sql: str, timeout_s: float = 10.0):
    """(오름차순 동점 처리 결과, 내림차순 동점 처리 결과). 최상위 ORDER BY가 없으면 None."""
    sql = sql.strip().rstrip(";")
    order_at, limit_at = top_level_order_by(sql)
    if order_at is None:
        return None
    columns, _ = execute(db_path, sql, timeout_s=timeout_s, max_rows=1)
    head, tail = (sql[:limit_at], sql[limit_at:]) if limit_at and limit_at > order_at else (sql, "")
    out = []
    for direction in ("ASC", "DESC"):
        extra = ", ".join(f"{i} {direction}" for i in range(1, len(columns) + 1))
        out.append(execute(db_path, f"{head.rstrip()}, {extra} {tail}", timeout_s=timeout_s)[1])
    return out[0], out[1]


def tie_blocks(a: list[tuple], b: list[tuple]) -> list[tuple[int, int]]:
    """두 정렬 결과에서 동점 묶음 [시작, 끝) 목록. 앞부분 행 집합이 같아지는 지점이 경계."""
    blocks, start = [], 0
    ca, cb = Counter(), Counter()
    for k in range(len(a)):
        ca[a[k]] += 1
        cb[b[k]] += 1
        if ca == cb:
            blocks.append((start, k + 1))
            start = k + 1
    if start < len(a):
        blocks.append((start, len(a)))
    return blocks


def match_with_ties(pred_rows: list[tuple], a: list[tuple], b: list[tuple]) -> bool:
    """동점 묶음 안에서는 순서를 따지지 않고, 묶음 사이의 순서는 엄격하게 비교한다."""
    if Counter(a) != Counter(b):
        # LIMIT 경계에서 동점이 갈려 정답 행 자체가 모호함: 이런 문항은 평가셋에서 미리 빼야 한다
        return False
    if len(pred_rows) != len(a):
        return False
    return all(Counter(pred_rows[s:e]) == Counter(a[s:e]) for s, e in tie_blocks(a, b))
