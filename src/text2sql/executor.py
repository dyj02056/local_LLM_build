"""모델이 만든 SQL을 안전하게 실행한다.

문자열 검사(예: "DROP" 포함 여부)는 우회가 쉽기 때문에 DB 계층에서 막는다.
  1. 읽기 전용(mode=ro)으로 연결
  2. authorizer로 SELECT/READ/FUNCTION 외의 모든 동작 거부 (PRAGMA, ATTACH 등 포함)
  3. progress handler로 실행 시간 제한
"""

import sqlite3
import time
from pathlib import Path

_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    getattr(sqlite3, "SQLITE_RECURSIVE", 33),
}


def _authorizer(action, arg1, arg2, db_name, source):
    return sqlite3.SQLITE_OK if action in _ALLOWED_ACTIONS else sqlite3.SQLITE_DENY


def connect_readonly(db_path: str | Path) -> sqlite3.Connection:
    db_path = Path(db_path).resolve()
    if not db_path.is_file():
        raise FileNotFoundError(db_path)
    conn = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True, check_same_thread=False)
    # Spider의 일부 DB에는 잘못된 UTF-8 바이트가 섞여 있다
    conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    conn.set_authorizer(_authorizer)
    return conn


def execute(
    db_path: str | Path, sql: str, timeout_s: float = 5.0, max_rows: int | None = None
) -> tuple[list[str], list[tuple]]:
    """SQL을 실행해 (컬럼명, 행 목록)을 반환한다. 실패 시 sqlite3.Error를 그대로 올린다."""
    conn = connect_readonly(db_path)
    deadline = time.monotonic() + timeout_s
    conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 10_000)
    try:
        cur = conn.execute(sql)
        columns = [d[0] for d in cur.description or []]
        rows = cur.fetchmany(max_rows) if max_rows else cur.fetchall()
        return columns, rows
    finally:
        conn.close()
