import shutil

import pytest
from fastapi.testclient import TestClient

import app.main as main


@pytest.fixture
def client(sample_db, tmp_path, monkeypatch):
    root = tmp_path / "korean"
    (root / "shop").mkdir(parents=True)
    shutil.copy(sample_db, root / "shop" / "shop.sqlite")
    monkeypatch.setattr(main, "KOREAN_DB_ROOT", root)
    monkeypatch.setattr(main, "SPIDER_DB_ROOT", tmp_path / "no_spider")
    return TestClient(main.app)


def fake_chat(answers):
    calls = []

    def _chat(messages, model=None, **_):
        calls.append(model)
        return answers[min(len(calls), len(answers)) - 1]

    return _chat, calls


def test_lists_only_existing_databases(client):
    assert client.get("/api/databases").json() == [{"id": "shop", "group": "korean"}]


def test_rejects_path_traversal(client):
    r = client.post("/api/query", json={"db_id": "../etc", "question": "q"})
    assert r.status_code == 400


def test_query_returns_rows_with_selected_model(client, monkeypatch):
    chat_fn, calls = fake_chat(["SELECT name FROM customer WHERE city = 'Seoul'"])
    monkeypatch.setattr(main, "chat", chat_fn)
    r = client.post("/api/query", json={"db_id": "shop", "question": "서울 고객", "model": "base"})
    body = r.json()
    assert r.status_code == 200 and body["error"] is None
    assert sorted(body["rows"]) == [["Kim"], ["Park"]]
    assert calls == [main.MODELS["base"]]


def test_sql_error_is_reported_not_raised(client, monkeypatch):
    chat_fn, _ = fake_chat(["SELECT nam FROM customer"])
    monkeypatch.setattr(main, "chat", chat_fn)
    body = client.post("/api/query", json={"db_id": "shop", "question": "q"}).json()
    assert "no such column" in body["error"] and body["attempts"] == []


def test_self_correction_reports_voided_attempts(client, monkeypatch):
    chat_fn, calls = fake_chat(["SELECT nam FROM customer", "SELECT name FROM customer"])
    monkeypatch.setattr(main, "chat", chat_fn)
    body = client.post("/api/query", json={"db_id": "shop", "question": "q", "self_correct": True}).json()
    assert body["error"] is None and body["sql"] == "SELECT name FROM customer"
    assert body["attempts"] == [{"sql": "SELECT nam FROM customer", "error": "no such column: nam"}]
    assert len(calls) == 2


def test_writes_are_blocked(client, monkeypatch):
    chat_fn, _ = fake_chat(["DELETE FROM customer"])
    monkeypatch.setattr(main, "chat", chat_fn)
    body = client.post("/api/query", json={"db_id": "shop", "question": "q"}).json()
    assert body["error"] is not None


def test_vote_picks_majority_result_and_reports_candidates(client, monkeypatch):
    answers = [
        "SELECT name FROM customer WHERE city = 'Seoul'",  # 베이스라인
        "SELECT name FROM customer",  # v3: 다른 결과
        "SELECT nam FROM customer",  # 베이스라인 + 예시 행: 실행 오류
        "SELECT name FROM customer WHERE city = 'Seoul'",  # v2
        "SELECT name FROM customer WHERE city = 'Seoul' ORDER BY name",  # v1: 같은 행 (순서 무시)
    ]
    chat_fn, calls = fake_chat(answers)
    monkeypatch.setattr(main, "chat", chat_fn)
    body = client.post("/api/query", json={"db_id": "shop", "question": "서울 고객", "model": "vote"}).json()
    assert body["error"] is None and sorted(body["rows"]) == [["Kim"], ["Park"]]
    assert calls == [main.MODELS[k] for k in ("base", "ft3", "base", "ft2", "ft")]
    vote = body["vote"]
    assert vote["votes"] == 3 and vote["total"] == 5
    assert [c["group"] for c in vote["candidates"]] == [1, 2, None, 1, 1]
    assert [c["picked"] for c in vote["candidates"]] == [True, False, False, False, False]
    assert "no such column" in vote["candidates"][2]["error"]
    assert vote["candidates"][2]["label"] == "베이스라인 + 예시 행"
