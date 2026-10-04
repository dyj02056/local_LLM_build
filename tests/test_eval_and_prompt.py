from text2sql.evaluate import evaluate_example, results_match
from text2sql.prompt import build_messages, extract_sql
from text2sql.schema import get_schema


def test_results_match_unordered():
    assert results_match([(1,), (2,)], [(2,), (1,)], ordered=False)
    assert not results_match([(1,), (1,)], [(1,)], ordered=False)


def test_results_match_ordered():
    assert not results_match([(1,), (2,)], [(2,), (1,)], ordered=True)


def test_equivalent_sql_is_correct(sample_db):
    gold = "SELECT name FROM customer WHERE city = 'Seoul'"
    pred = "SELECT c.name FROM customer AS c WHERE c.city IN ('Seoul')"
    assert evaluate_example(sample_db, pred, gold).correct


def test_wrong_and_broken_sql(sample_db):
    gold = "SELECT name FROM customer WHERE city = 'Seoul'"
    assert not evaluate_example(sample_db, "SELECT name FROM customer", gold).correct
    r = evaluate_example(sample_db, "SELECT nam FROM customer", gold)
    assert not r.correct and r.error


def test_extract_sql():
    assert extract_sql("```sql\nSELECT 1;\n```") == "SELECT 1"
    assert extract_sql("Here is the query:\nSELECT a FROM t; -- done") == "SELECT a FROM t"
    assert extract_sql("WITH x AS (SELECT 1) SELECT * FROM x") == "WITH x AS (SELECT 1) SELECT * FROM x"


def test_schema_and_messages(sample_db):
    schema = get_schema(sample_db, sample_rows=1)
    assert "CREATE TABLE customer" in schema and "sample rows" in schema
    msgs = build_messages(schema, "서울 고객은?", "SELECT 1")
    assert [m["role"] for m in msgs] == ["system", "user", "assistant"]
