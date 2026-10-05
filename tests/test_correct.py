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


def test_hint_lists_real_columns(sample_db):
    seen = []

    def fake_chat(messages, **_):
        seen.append(messages)
        return "SELECT name FROM customer"

    self_correct([], "SELECT nam FROM customer", sample_db, fake_chat, use_hint=True)
    prompt = seen[0][-1]["content"]
    assert "- customer: id, name, city" in prompt and "orders" in prompt


def test_resamples_when_model_repeats_itself(sample_db):
    temps = []

    def fake_chat(messages, temperature=0.0):
        temps.append(temperature)
        return "SELECT nam FROM customer" if temperature == 0 else "SELECT name FROM customer"

    sql, history = self_correct([], "SELECT nam FROM customer", sample_db, fake_chat, repeat_temperature=0.7)
    assert temps == [0.0, 0.7]
    assert sql == "SELECT name FROM customer" and history[0]["resampled"]


def test_stops_after_max_rounds(sample_db):
    calls = []

    def stubborn_chat(messages):
        calls.append(1)
        return "SELECT nope FROM customer"

    sql, history = self_correct([], "SELECT nam FROM customer", sample_db, stubborn_chat, max_rounds=2)
    assert len(calls) == 2 and history[-1]["error"]
