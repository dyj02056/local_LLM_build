import sqlite3

import pytest

from text2sql.evaluate import evaluate_example
from text2sql.ties import tie_blocks, top_level_order_by


@pytest.fixture
def tie_db(tmp_path):
    path = tmp_path / "t.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE city (name TEXT, n INTEGER);
        INSERT INTO city VALUES ('서울', 59), ('수원', 24), ('대전', 24), ('부산', 28), ('제주', 15);
    """)
    conn.commit()
    conn.close()
    return path


GOLD = "SELECT name, n FROM city ORDER BY n DESC"


def test_finds_only_top_level_order_by():
    sql = "SELECT a FROM t WHERE x IN (SELECT x FROM u ORDER BY x LIMIT 1) ORDER BY a DESC LIMIT 3"
    order_at, limit_at = top_level_order_by(sql)
    assert sql[order_at:].startswith("ORDER BY a") and sql[limit_at:] == "LIMIT 3"


def test_tie_blocks_group_equal_keys():
    a = [("서울", 59), ("부산", 28), ("대전", 24), ("수원", 24), ("제주", 15)]
    b = [("서울", 59), ("부산", 28), ("수원", 24), ("대전", 24), ("제주", 15)]
    assert tie_blocks(a, b) == [(0, 1), (1, 2), (2, 4), (4, 5)]


def test_tied_rows_may_swap_when_tie_aware(tie_db):
    swapped = "SELECT name, n FROM city ORDER BY n DESC, name DESC"
    other = "SELECT name, n FROM city ORDER BY n DESC, name ASC"
    assert evaluate_example(tie_db, swapped, GOLD, tie_aware=True).correct
    assert evaluate_example(tie_db, other, GOLD, tie_aware=True).correct


def test_non_tied_order_is_still_strict(tie_db):
    wrong = "SELECT name, n FROM city ORDER BY n ASC"
    assert not evaluate_example(tie_db, wrong, GOLD, tie_aware=True).correct


def test_default_scoring_is_unchanged(tie_db):
    # 기존 평가(Spider 등)와 숫자를 맞추기 위해 기본값은 엄격한 순서 비교 그대로
    a = evaluate_example(tie_db, "SELECT name, n FROM city ORDER BY n DESC, name ASC", GOLD).correct
    b = evaluate_example(tie_db, "SELECT name, n FROM city ORDER BY n DESC, name DESC", GOLD).correct
    assert a != b
