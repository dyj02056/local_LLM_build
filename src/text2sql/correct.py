"""Self-correction: 실행에 실패한 SQL을 오류 메시지와 함께 모델에 다시 보여 주고 고치게 한다.

정답 SQL은 쓰지 않는다. 실제 서비스에서도 알 수 있는 정보(SQLite 오류 메시지)만으로 재시도한다.
"""

import sqlite3
from collections.abc import Callable
from pathlib import Path

from .executor import execute
from .prompt import extract_sql

FIX_INSTRUCTION = (
    "The query failed with this SQLite error:\n{error}\n\n"
    "Fix the query. Use only the tables and columns defined in the schema above. "
    "Output only the corrected SQL query."
)


def run_error(db_path: str | Path, sql: str) -> str | None:
    """SQL을 실행해 보고 오류 메시지를 반환한다 (성공하면 None)."""
    try:
        execute(db_path, sql, max_rows=1)
        return None
    except sqlite3.Error as e:
        return str(e)


def build_fix_messages(messages: list[dict], bad_sql: str, error: str) -> list[dict]:
    return messages + [
        {"role": "assistant", "content": bad_sql},
        {"role": "user", "content": FIX_INSTRUCTION.format(error=error)},
    ]


def self_correct(
    messages: list[dict],
    sql: str,
    db_path: str | Path,
    chat_fn: Callable[[list[dict]], str],
    max_rounds: int = 2,
) -> tuple[str, list[dict]]:
    """실행 오류가 없어질 때까지 최대 max_rounds번 고친다.

    대화는 누적한다 (이전 시도와 오류를 모두 보여 줌). 반환: (최종 SQL, 시도 기록)
    """
    history = []
    error = run_error(db_path, sql)
    for _ in range(max_rounds):
        if error is None:
            break
        messages = build_fix_messages(messages, sql, error)
        raw = chat_fn(messages)
        sql = extract_sql(raw)
        error = run_error(db_path, sql)
        history.append({"sql": sql, "error": error, "raw": raw})
    return sql, history
