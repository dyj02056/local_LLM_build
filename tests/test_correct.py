from text2sql.correct import self_correct


def test_fixes_broken_sql_with_error_feedback(sample_db):
    seen = []

    def fake_chat(messages):
        seen.append(messages)
        return "```sql\nSELECT name FROM customer;\n```"

    sql, history = self_correct([{"role": "user", "content": "q"}], "SELECT nam FROM customer", sample_db, fake_chat)
    assert sql == "SELECT name FROM customer"
    assert len(history) == 1 and history[0]["error"] is None
    # 이전 SQL과 오류 메시지가 모델에 전달돼야 한다
    assert seen[0][-2] == {"role": "assistant", "content": "SELECT nam FROM customer"}
    assert "no such column" in seen[0][-1]["content"]


def test_valid_sql_is_not_sent_to_model(sample_db):
    def fail_chat(messages):
        raise AssertionError("실행되는 SQL은 모델을 다시 부르면 안 된다")

    sql, history = self_correct([], "SELECT name FROM customer", sample_db, fail_chat)
    assert sql == "SELECT name FROM customer" and history == []


def test_stops_after_max_rounds(sample_db):
    calls = []

    def stubborn_chat(messages):
        calls.append(1)
        return "SELECT nope FROM customer"

    sql, history = self_correct([], "SELECT nam FROM customer", sample_db, stubborn_chat, max_rounds=2)
    assert len(calls) == 2 and history[-1]["error"]
