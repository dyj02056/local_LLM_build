"""Text-to-SQL API 서버.

실행:
    uvicorn app.main:app --reload
환경변수: DB_ROOT (기본 data/spider/database), TEXT2SQL_MODEL, OLLAMA_URL
"""

import os
import re
import sqlite3
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from text2sql.executor import execute
from text2sql.llm import DEFAULT_MODEL, chat
from text2sql.prompt import build_messages, extract_sql
from text2sql.schema import db_path_for, get_schema

DB_ROOT = Path(os.environ.get("DB_ROOT", "data/spider/database"))
MAX_ROWS = 200
_DB_ID_RE = re.compile(r"^[A-Za-z0-9_]+$")

app = FastAPI(title="Local Text-to-SQL")


class QueryRequest(BaseModel):
    db_id: str
    question: str = Field(min_length=1, max_length=1000)


class QueryResponse(BaseModel):
    sql: str
    columns: list[str]
    rows: list[list]
    truncated: bool
    generation_ms: int
    execution_ms: int


def _resolve_db(db_id: str) -> Path:
    # db_id는 경로에 들어가므로 경로 조작(../) 차단
    if not _DB_ID_RE.match(db_id):
        raise HTTPException(400, "invalid db_id")
    path = db_path_for(DB_ROOT, db_id)
    if not path.is_file():
        raise HTTPException(404, f"database '{db_id}' not found")
    return path


@app.get("/health")
def health():
    return {"status": "ok", "model": DEFAULT_MODEL}


@app.get("/databases")
def list_databases():
    if not DB_ROOT.is_dir():
        return []
    return sorted(p.name for p in DB_ROOT.iterdir() if db_path_for(DB_ROOT, p.name).is_file())


@app.get("/schema/{db_id}")
def schema(db_id: str):
    return {"db_id": db_id, "schema": get_schema(_resolve_db(db_id))}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    db_path = _resolve_db(req.db_id)

    t0 = time.perf_counter()
    try:
        raw = chat(build_messages(get_schema(db_path), req.question))
    except httpx.HTTPError as e:
        raise HTTPException(502, f"LLM server error: {e}")
    sql = extract_sql(raw)
    t1 = time.perf_counter()

    try:
        columns, rows = execute(db_path, sql, timeout_s=5.0, max_rows=MAX_ROWS + 1)
    except sqlite3.Error as e:
        raise HTTPException(422, detail={"sql": sql, "error": str(e)})
    t2 = time.perf_counter()

    return QueryResponse(
        sql=sql,
        columns=columns,
        rows=[list(r) for r in rows[:MAX_ROWS]],
        truncated=len(rows) > MAX_ROWS,
        generation_ms=int((t1 - t0) * 1000),
        execution_ms=int((t2 - t1) * 1000),
    )
