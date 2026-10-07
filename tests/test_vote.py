import pytest

from text2sql.vote import vote


def test_majority_wins_over_first(sample_db):
    seoul = "SELECT name FROM customer WHERE city = 'Seoul'"
    seoul2 = "SELECT c.name FROM customer AS c WHERE c.city IN ('Seoul')"
    r = vote(sample_db, ["SELECT name FROM customer", seoul, seoul2])
    assert r.index == 1 and r.votes == 2


def test_row_order_is_ignored(sample_db):
    a = "SELECT name FROM customer ORDER BY id"
    b = "SELECT name FROM customer ORDER BY id DESC"
    assert vote(sample_db, ["SELECT 1", a, b]).votes == 2


def test_tie_prefers_earlier_candidate(sample_db):
    r = vote(sample_db, ["SELECT sum(amount) FROM orders", "SELECT count(*) FROM customer"])
    assert r.index == 0 and r.votes == 1


def test_failed_sql_has_no_vote(sample_db):
    r = vote(sample_db, ["SELECT nam FROM customer", "SELECT nam FROM customer", "SELECT 1"])
    assert r.index == 2 and r.votes == 1


def test_all_failed_returns_first(sample_db):
    r = vote(sample_db, ["SELECT x FROM nowhere", "DROP TABLE customer"])
    assert r.index == 0 and r.votes == 0


def test_empty_candidates(sample_db):
    with pytest.raises(ValueError):
        vote(sample_db, [])
