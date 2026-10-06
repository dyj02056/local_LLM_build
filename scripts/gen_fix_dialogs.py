"""오류 수정 대화 학습 데이터: "틀린 SQL → 실제 SQLite 오류 → 고친 SQL".

    python scripts/gen_fix_dialogs.py                       # -> data/korean_train/fix_dialogs.jsonl
    python scripts/gen_fix_dialogs.py --spider-n 300        # Spider train DB로 만든 대화도 섞기

자동수정 실험에서 3B 모델은 오류 메시지를 받고도 직전 SQL을 그대로 반복했다 (v1 40%, 베이스라인 65%).
지시문을 바꾸는 것으로는 고쳐지지 않아서, 고치는 법 자체를 학습 데이터로 보여 준다.

- 정답 SQL을 일부러 망가뜨려 실제로 실행하고, SQLite가 낸 오류 메시지를 그대로 쓴다.
  망가뜨리는 방식은 실험에서 실제로 본 오류 유형이다:
    컬럼 이름 틀림(pet_type ↔ PetType), 별칭 혼동(T2.x ↔ T1.x), 중간 테이블 누락,
    모호한 컬럼(별칭 빠짐), 테이블 이름 틀림
- 대화 형식은 src/text2sql/correct.py의 build_fix_messages()와 똑같다 (추론 때 보는 모양 그대로).
- 학습 DB는 한국어 학습용 4개(도서관, 병원, 학원, 여행사)와 Spider train DB만 쓴다.
  평가용 쇼핑몰(shop)과 Spider dev DB는 쓰지 않는다.

⚠ 학습할 때 첫 번째 assistant 턴(틀린 SQL)까지 Loss를 계산하면 틀린 SQL을 배운다.
  train/finetune_unsloth.py의 "마지막 응답만 학습" 셀로 고친 SQL에만 Loss를 건다.
"""

import argparse
import json
import random
import re
import sqlite3
from collections import Counter
from pathlib import Path

from text2sql.correct import build_fix_messages, run_error
from text2sql.prompt import build_messages
from text2sql.schema import db_path_for, get_columns, get_schema

ALIAS_RE = re.compile(r"\b(\w+)\s+AS\s+(T\d+)\b", re.IGNORECASE)
QUAL_RE = re.compile(r"\b(T\d+)\.(\w+)\b", re.IGNORECASE)  # Spider는 t1처럼 소문자 별칭도 씀
JOIN_RE = re.compile(r"\s+JOIN\s+(\w+)\s+AS\s+(T\d+)\s+ON\s+[\w.]+\s*=\s*[\w.]+", re.IGNORECASE)


def snake_to_camel(name: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in name.split("_") if p)


def camel_to_snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


def name_variants(name: str) -> list[str]:
    """학습 데이터 말투에 끌려 모델이 지어내는 이름들 (예: PetType -> pet_type, name -> names)."""
    out = []
    if "_" in name:
        out += [snake_to_camel(name), name.replace("_", "")]
    elif re.search(r"[a-z][A-Z]", name):
        out.append(camel_to_snake(name))
    out += [name + "s", name + "_name", name + "_id"] if not name.endswith("s") else [name[:-1]]
    return [v for v in out if v.lower() != name.lower()]


class Corruptor:
    def __init__(self, columns: dict[str, list[str]]):
        self.columns = {t.lower(): {c.lower() for c in cols} for t, cols in columns.items()}
        self.all_cols = set().union(*self.columns.values()) if self.columns else set()

    def aliases(self, sql):
        return {a.lower(): t.lower() for t, a in ALIAS_RE.findall(sql) if t.lower() in self.columns}

    def bad_column(self, sql, rnd):
        cands = [m for m in re.finditer(r"\b\w+\b", sql) if m.group().lower() in self.all_cols
                 and not sql[: m.start()].rstrip().upper().endswith(("FROM", "JOIN", "AS"))]
        rnd.shuffle(cands)
        for m in cands:
            for v in name_variants(m.group()):
                if v.lower() not in self.all_cols and v.lower() not in self.columns:
                    return sql[: m.start()] + v + sql[m.end():]
        return None

    def wrong_alias(self, sql, rnd):
        al = self.aliases(sql)
        cands = list(QUAL_RE.finditer(sql))
        rnd.shuffle(cands)
        for m in cands:
            a, col = m.group(1).lower(), m.group(2).lower()
            others = [b for b, t in al.items() if b != a and col not in self.columns[t]]
            if a in al and others:
                return sql[: m.start()] + rnd.choice(others) + "." + m.group(2) + sql[m.end():]
        return None

    def drop_join(self, sql, rnd):
        """JOIN 2개 이상에서 중간 테이블 하나를 빼서, 그 별칭을 쓰는 곳이 깨지게 한다 (v1의 order_items 누락)."""
        joins = list(JOIN_RE.finditer(sql))
        if len(joins) < 2:
            return None
        m = rnd.choice(joins[:-1])
        return sql[: m.start()] + sql[m.end():]

    def ambiguous(self, sql, rnd):
        al = self.aliases(sql)
        cands = [m for m in QUAL_RE.finditer(sql)
                 if sum(m.group(2).lower() in self.columns[t] for t in set(al.values())) >= 2]
        if not cands:
            return None
        m = rnd.choice(cands)
        return sql[: m.start()] + m.group(2) + sql[m.end():]

    def bad_table(self, sql, rnd):
        tables = [m for m in re.finditer(r"\b(FROM|JOIN)\s+(\w+)", sql, re.IGNORECASE) if m.group(2).lower() in self.columns]
        if not tables:
            return None
        m = rnd.choice(tables)
        t = m.group(2)
        v = t[:-1] if t.endswith("s") else t + "s"
        if v.lower() in self.columns:
            return None
        return sql[: m.start(2)] + v + sql[m.end(2):]


KINDS = ["bad_column", "wrong_alias", "drop_join", "ambiguous", "bad_table"]
WEIGHTS = {"bad_column": 3, "wrong_alias": 3, "drop_join": 3, "ambiguous": 2, "bad_table": 1}


def make_dialogs(rows, db_root, n, rnd):
    caches, out, kinds = {}, [], Counter()
    rnd.shuffle(rows)
    for r in rows:
        if len(out) >= n:
            break
        db = r["db_id"]
        if db not in caches:
            path = db_path_for(db_root, db)
            caches[db] = (path, get_schema(path), Corruptor(get_columns(path)))
        path, schema, cor = caches[db]
        good = r["query"].strip().rstrip(";")
        if run_error(path, good) is not None:
            continue
        # 가중치가 큰 방식부터 시도하되 순서는 매번 섞는다. 해당 방식이 안 되면 다음 방식으로
        order = sorted(KINDS, key=lambda k: -WEIGHTS[k] * rnd.random())
        for kind in order:
            bad = getattr(cor, kind)(good, rnd)
            if not bad or bad == good:
                continue
            try:
                error = run_error(path, bad)
            except Exception:
                error = None
            if not error:  # 망가뜨렸는데 실행이 되면(결과만 틀림) 오류 수정 예시가 아니므로 버린다
                continue
            messages = build_fix_messages(build_messages(schema, r["question"]), bad, error)
            messages.append({"role": "assistant", "content": good})
            out.append({"db_id": db, "question": r["question"], "query": good, "bad_sql": bad,
                        "error": error, "kind": kind, "messages": messages})
            kinds[kind] += 1
            break
    return out, kinds


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--korean", default="data/korean_train/train_ko_v3.jsonl")
    ap.add_argument("--korean-root", default="data/korean_train/database")
    ap.add_argument("--korean-n", type=int, default=300)
    ap.add_argument("--spider", default="data/sft/train.jsonl")
    ap.add_argument("--spider-root", default="data/spider/database")
    ap.add_argument("--spider-n", type=int, default=0, help="Spider train DB로 만들 대화 수 (0이면 안 씀)")
    ap.add_argument("--out", default="data/korean_train/fix_dialogs.jsonl")
    ap.add_argument("--seed", type=int, default=17)
    args = ap.parse_args()
    rnd = random.Random(args.seed)

    dialogs, kinds = make_dialogs(load(args.korean), args.korean_root, args.korean_n, rnd)
    if args.spider_n:
        sp, k2 = make_dialogs(load(args.spider), args.spider_root, args.spider_n, rnd)
        dialogs += sp
        kinds += k2
    rnd.shuffle(dialogs)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for d in dialogs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    errors = Counter(re.sub(r":.*", "", d["error"]) for d in dialogs)
    print(f"{len(dialogs)}개 -> {args.out}")
    print("망가뜨린 방식:", dict(kinds))
    print("SQLite 오류 종류:", dict(errors.most_common()))


if __name__ == "__main__":
    main()
