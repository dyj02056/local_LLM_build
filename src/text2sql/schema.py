"""SQLite DB에서 프롬프트에 넣을 스키마 텍스트를 만든다."""

from pathlib import Path

from .executor import connect_readonly


def db_path_for(db_root: str | Path, db_id: str) -> Path:
    """Spider 레이아웃: <db_root>/<db_id>/<db_id>.sqlite"""
    return Path(db_root) / db_id / f"{db_id}.sqlite"


def get_schema(db_path: str | Path, sample_rows: int = 0) -> str:
    """CREATE TABLE 문을 이어 붙인 스키마. sample_rows > 0이면 테이블별 예시 행을 주석으로 덧붙인다."""
    conn = connect_readonly(db_path)
    try:
        tables = conn.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        parts = []
        for name, ddl in tables:
            block = ddl.strip()
            if sample_rows:
                rows = conn.execute(f'SELECT * FROM "{name}" LIMIT {int(sample_rows)}').fetchall()
                if rows:
                    block += "\n/* sample rows:\n" + "\n".join(map(str, rows)) + "\n*/"
            parts.append(block)
        return "\n\n".join(parts)
    finally:
        conn.close()


def get_columns(db_path: str | Path) -> dict[str, list[str]]:
    """테이블별 실제 컬럼 이름. (authorizer가 PRAGMA를 막으므로 빈 SELECT의 description으로 읽는다)"""
    conn = connect_readonly(db_path)
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return {t: [d[0] for d in conn.execute(f'SELECT * FROM "{t}" LIMIT 0').description] for (t,) in tables}
    finally:
        conn.close()
