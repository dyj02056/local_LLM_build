import sqlite3

import pytest

from text2sql.executor import execute


def test_select(sample_db):
    columns, rows = execute(sample_db, "SELECT name FROM customer WHERE city = 'Seoul' ORDER BY id")
    assert columns == ["name"]
    assert rows == [("Kim",), ("Park",)]


def test_cte_and_join(sample_db):
    sql = """
        WITH totals AS (SELECT customer_id, SUM(amount) AS s FROM orders GROUP BY customer_id)
        SELECT c.name, t.s FROM customer c JOIN totals t ON c.id = t.customer_id ORDER BY t.s DESC
    """
    assert execute(sample_db, sql)[1] == [("Kim", 350), ("Lee", 80)]


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE customer",
        "DELETE FROM customer",
        "UPDATE customer SET name = 'x'",
        "INSERT INTO customer VALUES (9, 'x', 'y')",
        "PRAGMA table_info(customer)",
        "ATTACH DATABASE 'evil.db' AS evil",
        "SELECT 1; DROP TABLE customer",
    ],
)
def test_blocks_non_select(sample_db, sql):
    with pytest.raises(sqlite3.Error):
        execute(sample_db, sql)
    # 테이블이 그대로 남아 있어야 한다
    assert len(execute(sample_db, "SELECT * FROM customer")[1]) == 3


def test_timeout(sample_db):
    infinite = "WITH RECURSIVE r(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM r) SELECT count(*) FROM r"
    with pytest.raises(sqlite3.OperationalError):
        execute(sample_db, infinite, timeout_s=0.3)


def test_max_rows(sample_db):
    assert len(execute(sample_db, "SELECT * FROM customer", max_rows=2)[1]) == 2
