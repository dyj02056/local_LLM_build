"""학습·추론에서 똑같이 쓰는 프롬프트 형식.

학습 데이터와 추론 프롬프트가 조금이라도 다르면 파인튜닝 효과가 크게 떨어지므로
반드시 이 모듈 하나만 거쳐서 만든다.
"""

import re

SYSTEM_PROMPT = (
    "You are an expert SQLite assistant. Given a database schema and a question, "
    "write a single SQLite SELECT query that answers the question. "
    "Output only the SQL query, without explanation."
)


def build_messages(schema: str, question: str, answer_sql: str | None = None) -> list[dict]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"### Schema\n{schema}\n\n### Question\n{question}"},
    ]
    if answer_sql is not None:
        messages.append({"role": "assistant", "content": answer_sql.strip()})
    return messages


_FENCE_RE = re.compile(r"```(?:sql|sqlite)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_sql(text: str) -> str:
    """모델 출력에서 SQL 한 문장만 뽑는다 (코드 펜스, 설명문, 여러 문장 대응)."""
    m = _FENCE_RE.search(text)
    sql = m.group(1) if m else text
    sql = sql.strip()
    # 첫 SELECT/WITH부터 시작하도록 앞쪽 설명문 제거
    start = re.search(r"\b(SELECT|WITH)\b", sql, re.IGNORECASE)
    if start:
        sql = sql[start.start():]
    # 첫 번째 문장만 사용
    sql = sql.split(";")[0].strip()
    return sql
