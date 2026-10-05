"""Text-to-SQL API 서버 + 데모 화면.

실행:
    uvicorn app.main:app --reload
화면: web/ 을 빌드(npm run build)하면 web/dist 를 / 에서 함께 제공한다.

환경변수:
    KOREAN_DB_ROOT  한국어 쇼핑몰 DB 폴더 (기본 data/korean/database)
    DB_ROOT         Spider DB 폴더 (기본 data/spider/database)
    BASE_MODEL      베이스라인 모델 (기본 qwen2.5-coder:3b)
    FT_MODEL        파인튜닝 모델 (기본 text2sql-ft)
    OLLAMA_URL
"""

import json
import os
import re
import sqlite3
import time
from functools import partial
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from text2sql.correct import run_error, self_correct
from text2sql.executor import execute
from text2sql.llm import OLLAMA_URL, chat
from text2sql.prompt import build_messages, extract_sql
from text2sql.schema import db_path_for, get_schema

ROOT = Path(__file__).resolve().parent.parent
KOREAN_DB_ROOT = Path(os.environ.get("KOREAN_DB_ROOT", ROOT / "data/korean/database"))
SPIDER_DB_ROOT = Path(os.environ.get("DB_ROOT", ROOT / "data/spider/database"))
SPIDER_DEV_JSON = SPIDER_DB_ROOT.parent / "dev.json"
MODELS = {
    "base": os.environ.get("BASE_MODEL", "qwen2.5-coder:3b"),
    "ft": os.environ.get("FT_MODEL", "text2sql-ft"),
}
MAX_ROWS = 200
_DB_ID_RE = re.compile(r"^[A-Za-z0-9_]+$")

app = FastAPI(title="Local Text-to-SQL")
api = APIRouter(prefix="/api")


def _databases() -> list[dict]:
    """화면에 보여 줄 DB 목록. 한국어 쇼핑몰 DB가 먼저, 그다음 Spider dev DB."""
    dbs = []
    if db_path_for(KOREAN_DB_ROOT, "shop").is_file():
        dbs.append({"id": "shop", "group": "korean", "root": KOREAN_DB_ROOT})
    if SPIDER_DB_ROOT.is_dir():
        if SPIDER_DEV_JSON.is_file():
            ids = sorted({ex["db_id"] for ex in json.loads(SPIDER_DEV_JSON.read_text(encoding="utf-8"))})
        else:
            ids = sorted(p.name for p in SPIDER_DB_ROOT.iterdir())
        dbs += [{"id": i, "group": "spider", "root": SPIDER_DB_ROOT}
                for i in ids if db_path_for(SPIDER_DB_ROOT, i).is_file()]
    return dbs


def _resolve_db(db_id: str) -> Path:
    # db_id는 경로에 들어가므로 경로 조작(../) 차단
    if not _DB_ID_RE.match(db_id):
        raise HTTPException(400, "invalid db_id")
    for db in _databases():
        if db["id"] == db_id:
            return db_path_for(db["root"], db_id)
    raise HTTPException(404, f"database '{db_id}' not found")


class QueryRequest(BaseModel):
    db_id: str
    question: str = Field(min_length=1, max_length=1000)
    model: Literal["base", "ft"] = "ft"
    self_correct: bool = False


class Attempt(BaseModel):
    sql: str
    error: str | None


class QueryResponse(BaseModel):
    model: str
    sql: str
    columns: list[str]
    rows: list[list]
    truncated: bool
    error: str | None  # 최종 SQL도 실행에 실패하면 SQLite 오류 메시지
    attempts: list[Attempt]  # self-correction 이전 시도들 (첫 시도 포함, 최종 제외)
    generation_ms: int
    execution_ms: int


@api.get("/health")
def health():
    try:
        tags = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3).json()
        installed = {m["name"].removesuffix(":latest") for m in tags.get("models", [])}
        ollama = True
    except (httpx.HTTPError, ValueError):
        installed, ollama = set(), False
    return {
        "status": "ok",
        "ollama": ollama,
        "models": {k: {"name": v, "installed": v.removesuffix(":latest") in installed} for k, v in MODELS.items()},
    }


@api.get("/databases")
def list_databases():
    return [{"id": d["id"], "group": d["group"]} for d in _databases()]


@api.get("/schema/{db_id}")
def schema(db_id: str):
    return {"db_id": db_id, "schema": get_schema(_resolve_db(db_id))}


@api.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    db_path = _resolve_db(req.db_id)
    model = MODELS[req.model]
    messages = build_messages(get_schema(db_path), req.question)
    chat_fn = partial(chat, model=model)

    t0 = time.perf_counter()
    try:
        sql = extract_sql(chat_fn(messages))
        attempts = []
        if req.self_correct:
            first = sql
            sql, history = self_correct(messages, sql, db_path, chat_fn)
            if history:
                voided = [(first, run_error(db_path, first))] + [(h["sql"], h["error"]) for h in history[:-1]]
                attempts = [Attempt(sql=s, error=e) for s, e in voided]
    except httpx.HTTPError as e:
        raise HTTPException(502, f"LLM 서버에 연결할 수 없습니다: {e}")
    t1 = time.perf_counter()

    columns, rows, error = [], [], None
    try:
        columns, rows = execute(db_path, sql, timeout_s=5.0, max_rows=MAX_ROWS + 1)
    except sqlite3.Error as e:
        error = str(e)
    t2 = time.perf_counter()

    return QueryResponse(
        model=model,
        sql=sql,
        columns=columns,
        rows=[list(r) for r in rows[:MAX_ROWS]],
        truncated=len(rows) > MAX_ROWS,
        error=error,
        attempts=attempts,
        generation_ms=int((t1 - t0) * 1000),
        execution_ms=int((t2 - t1) * 1000),
    )


app.include_router(api)

# 빌드된 화면이 있으면 / 에서 제공 (API 라우트 뒤에 마운트해야 /api 가 가려지지 않음)
_DIST = ROOT / "web" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="web")
