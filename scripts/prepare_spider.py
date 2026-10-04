"""Spider 원본을 SFT용 chat JSONL로 변환한다.

사용법:
    python scripts/prepare_spider.py --spider-dir data/spider --out-dir data/sft

출력 각 줄: {"db_id", "question", "query", "messages": [system, user, assistant]}
"""

import argparse
import json
from pathlib import Path

from text2sql.prompt import build_messages
from text2sql.schema import db_path_for, get_schema

SPLITS = {
    "train": ["train_spider.json", "train_others.json"],
    "dev": ["dev.json"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spider-dir", default="data/spider")
    ap.add_argument("--out-dir", default="data/sft")
    ap.add_argument("--sample-rows", type=int, default=0, help="스키마에 넣을 테이블별 예시 행 수")
    args = ap.parse_args()

    spider_dir = Path(args.spider_dir)
    db_root = spider_dir / "database"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    schema_cache: dict[str, str] = {}

    for split, files in SPLITS.items():
        n, skipped = 0, 0
        with open(out_dir / f"{split}.jsonl", "w", encoding="utf-8") as fout:
            for fname in files:
                path = spider_dir / fname
                if not path.exists():
                    print(f"[skip] {path} 없음")
                    continue
                for ex in json.loads(path.read_text(encoding="utf-8")):
                    db_id = ex["db_id"]
                    if db_id not in schema_cache:
                        db_path = db_path_for(db_root, db_id)
                        schema_cache[db_id] = get_schema(db_path, args.sample_rows) if db_path.exists() else None
                    schema = schema_cache[db_id]
                    if schema is None:
                        skipped += 1
                        continue
                    record = {
                        "db_id": db_id,
                        "question": ex["question"],
                        "query": ex["query"],
                        "messages": build_messages(schema, ex["question"], ex["query"]),
                    }
                    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                    n += 1
        print(f"{split}: {n}개 작성, DB 없음으로 {skipped}개 제외 -> {out_dir / f'{split}.jsonl'}")
        if n == 0:
            raise SystemExit(f"{split} 데이터가 0개입니다. {db_root} 에 DB 압축이 다 풀렸는지 확인하세요.")


if __name__ == "__main__":
    main()
