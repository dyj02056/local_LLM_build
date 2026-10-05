"""Self-correction: 실행에 실패한 SQL을 오류 메시지와 함께 모델에 다시 보여 주고 고치게 한다.

정답 SQL은 쓰지 않는다. 실제 서비스에서도 알 수 있는 정보(SQLite 오류 메시지, DB 스키마)만으로 재시도한다.
"""

import sqlite3
from collections.abc import Callable
from pathlib import Path

from .executor import execute
from .prompt import extract_sql
from .schema import get_columns

FIX_INSTRUCTION = (
    "The query failed with this SQLite error:\n{error}\n\n"
    "Fix the query. Use only the tables and columns defined in the schema above. "
    "Output only the corrected SQL query."
)

HINT_INSTRUCTION = (
    "The query failed with this SQLite error:\n{error}\n\n"
    "These are the only valid tables and their exact column names:\n{columns}\n\n"
    "Write a corrected query that uses only these names. "
    "Do not repeat the previous query unchanged. Output only the corrected SQL query."
)


def run_error(db_path: str | Path, sql: str) -> str | None:
    """SQL을 실행해 보고 오류 메시지를 반환한다 (성공하면 None)."""
    try:
        execute(db_path, sql, max_rows=1)
        return None
    except sqlite3.Error as e:
        return str(e)


def column_hint(db_path: str | Path) -> str:
    return "\n".join(f"- {t}: {', '.join(cols)}" for t, cols in get_columns(db_path).items())


def build_fix_messages(messages: list[dict], bad_sql: str, error: str, hint: str | None = None) -> list[dict]:
    if hint:
        content = HINT_INSTRUCTION.format(error=error, columns=hint)
    else:
        content = FIX_INSTRUCTION.format(error=error)
    return messages + [
        {"role": "assistant", "content": bad_sql},
        {"role": "user", "content": content},
    ]


def self_correct(
    messages: list[dict],
    sql: str,
    db_path: str | Path,
    chat_fn: Callable[..., str],
    max_rounds: int = 2,
    use_hint: bool = False,
    repeat_temperature: float | None = None,
) -> tuple[str, list[dict]]:
    """실행 오류가 없어질 때까지 최대 max_rounds번 고친다.

    대화는 누적한다 (이전 시도와 오류를 모두 보여 줌).
    use_hint: 오류 메시지와 함께 테이블별 실제 컬럼 목록을 준다.
    repeat_temperature: 이미 시도한 SQL이 또 나오면 이 temperature로 한 번 더 샘플링한다.
    반환: (최종 SQL, 시도 기록)
    """
    history = []
    tried = {sql}
    error = run_error(db_path, sql)
    hint = column_hint(db_path) if use_hint and error else None
    for _ in range(max_rounds):
        if error is None:
            break
        messages = build_fix_messages(messages, sql, error, hint)
        raw = chat_fn(messages)
        new_sql = extract_sql(raw)
        resampled = False
        if repeat_temperature and new_sql in tried:
            raw = chat_fn(messages, temperature=repeat_temperature)
            new_sql = extract_sql(raw)
            resampled = True
        sql = new_sql
        tried.add(sql)
        error = run_error(db_path, sql)
        history.append({"sql": sql, "error": error, "raw": raw, "resampled": resampled})
    return sql, history
