"""한국어 평가용 가상 쇼핑몰 SQLite DB를 만든다.

사용법:
    python scripts/build_shop_db.py
결과: data/korean/database/shop/shop.sqlite (Spider와 같은 <db_root>/<db_id>/<db_id>.sqlite 구조)

테이블·컬럼 이름은 영어, 값은 한국어 (국내 서비스 DB에서 흔한 형태).
seed가 고정돼 있어 언제 실행해도 같은 데이터가 만들어진다.
"""

import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SCHEMA = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    gender TEXT NOT NULL,          -- 'M' 또는 'F'
    birth_year INTEGER NOT NULL,
    city TEXT NOT NULL,
    grade TEXT NOT NULL,           -- '일반', '실버', '골드', 'VIP'
    joined_at DATE NOT NULL
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    brand TEXT NOT NULL,
    price INTEGER NOT NULL,        -- 원
    stock INTEGER NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    status TEXT NOT NULL,          -- '배송완료', '배송중', '결제완료', '취소'
    payment_method TEXT NOT NULL   -- '카드', '계좌이체', '간편결제'
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL    -- 주문 당시 가격 (원)
);

CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    rating INTEGER NOT NULL,       -- 1~5
    created_at DATE NOT NULL
);
"""

SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권"]
GIVEN = ["민준", "서연", "도윤", "지우", "하준", "서윤", "시우", "지민", "주원", "하은", "예준", "수아",
         "지호", "지유", "준서", "채원", "현우", "다은", "건우", "예린", "우진", "소율", "선우", "지아"]
CITIES = ["서울", "서울", "서울", "부산", "인천", "대구", "대전", "광주", "수원", "제주"]
GRADES = ["일반"] * 5 + ["실버"] * 3 + ["골드"] * 2 + ["VIP"]

# (카테고리, [(상품명, 브랜드, 가격)])
CATALOG = [
    ("전자제품", [("무선 이어폰", "소리샘", 129000), ("블루투스 스피커", "소리샘", 89000),
               ("27인치 모니터", "화면나라", 259000), ("기계식 키보드", "타건", 119000),
               ("무선 마우스", "타건", 39000), ("보조배터리 20000mAh", "충전왕", 45000),
               ("스마트워치", "화면나라", 299000)]),
    ("의류", [("기본 반팔 티셔츠", "데일리웨어", 15900), ("청바지", "데일리웨어", 49000),
             ("후드 집업", "어반핏", 59000), ("경량 패딩", "어반핏", 129000),
             ("면 양말 5족", "데일리웨어", 9900), ("린넨 셔츠", "어반핏", 45000)]),
    ("식품", [("유기농 현미 4kg", "들녘", 24900), ("제주 감귤 5kg", "들녘", 29900),
             ("콜드브루 원액", "아침커피", 18900), ("견과류 30봉", "든든", 27900),
             ("그릭요거트 6개입", "목장", 12900), ("닭가슴살 10팩", "든든", 21900)]),
    ("도서", [("파이썬 첫걸음", "코딩출판", 25000), ("SQL 실전 입문", "코딩출판", 28000),
             ("데이터 분석 입문", "코딩출판", 32000), ("한국사 이야기", "역사책방", 18000),
             ("에세이 모음집", "글밭", 15000)]),
    ("뷰티", [("수분 크림", "맑은피부", 32000), ("선크림 SPF50", "맑은피부", 19800),
             ("클렌징 폼", "맑은피부", 11900), ("립밤 3종", "꽃잎", 13500),
             ("헤어 에센스", "꽃잎", 16900)]),
    ("스포츠", [("요가 매트", "운동가", 29000), ("덤벨 5kg 세트", "운동가", 39000),
              ("러닝화", "달리기", 89000), ("등산 배낭 30L", "산마루", 79000),
              ("스포츠 물병", "달리기", 12000)]),
    ("가구", [("원목 책상", "나무공방", 189000), ("사무용 의자", "나무공방", 149000),
             ("3단 책장", "나무공방", 79000), ("접이식 테이블", "편한집", 59000)]),
    ("완구", [("블록 장난감 500피스", "놀이터", 45000), ("보드게임", "놀이터", 32000),
             ("인형", "포근", 19900)]),
]


def build(path: Path, seed: int = 42):
    rnd = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)

    # 고객 200명 (가입일 2023-01-01 ~ 2025-06-30)
    customers = []
    used_names = set()
    for cid in range(1, 201):
        while True:
            name = rnd.choice(SURNAMES) + rnd.choice(GIVEN)
            if name not in used_names:  # 이름으로 묻는 질문이 모호하지 않도록 중복 금지
                used_names.add(name)
                break
        joined = date(2023, 1, 1) + timedelta(days=rnd.randrange(0, 912))
        customers.append((cid, name, rnd.choice("MF"), rnd.randint(1965, 2005),
                          rnd.choice(CITIES), rnd.choice(GRADES), joined.isoformat()))
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?)", customers)

    # 카테고리, 상품
    products = []
    pid = 1
    for cat_id, (cat, items) in enumerate(CATALOG, start=1):
        conn.execute("INSERT INTO categories VALUES (?,?)", (cat_id, cat))
        for name, brand, price in items:
            products.append((pid, name, cat_id, brand, price, rnd.choice([0, 0] + list(range(3, 200)))))
            pid += 1
    conn.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products)

    # 주문 800건 (2025-01-01 ~ 2025-12-31). 인기 상품 쏠림을 주려고 가중치 사용
    weights = [rnd.uniform(0.2, 3.0) for _ in products]
    statuses = ["배송완료"] * 14 + ["배송중"] * 2 + ["결제완료"] * 2 + ["취소"] * 2
    payments = ["카드"] * 5 + ["간편결제"] * 4 + ["계좌이체"] * 2
    item_id = 1
    for oid in range(1, 801):
        c = rnd.choice(customers)
        joined = date.fromisoformat(c[6])
        start = max(joined, date(2025, 1, 1))
        od = start + timedelta(days=rnd.randrange(0, (date(2025, 12, 31) - start).days + 1))
        conn.execute("INSERT INTO orders VALUES (?,?,?,?,?)",
                     (oid, c[0], od.isoformat(), rnd.choice(statuses), rnd.choice(payments)))
        chosen = set()
        for _ in range(rnd.choices([1, 2, 3], [6, 3, 1])[0]):
            p = rnd.choices(products, weights)[0]
            if p[0] in chosen:
                continue
            chosen.add(p[0])
            # 일부 주문은 할인가로 판매
            unit = p[4] if rnd.random() < 0.8 else round(p[4] * 0.9, -2)
            conn.execute("INSERT INTO order_items VALUES (?,?,?,?,?)",
                         (item_id, oid, p[0], rnd.choices([1, 2, 3], [7, 2, 1])[0], int(unit)))
            item_id += 1

    # 리뷰: 배송완료 주문의 일부 상품에 작성
    rows = conn.execute("""
        SELECT o.customer_id, oi.product_id, o.order_date
        FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status = '배송완료' ORDER BY oi.order_item_id
    """).fetchall()
    rid = 1
    for customer_id, product_id, od in rows:
        if rnd.random() < 0.45:
            created = date.fromisoformat(od) + timedelta(days=rnd.randint(2, 20))
            rating = rnd.choices([1, 2, 3, 4, 5], [1, 1, 3, 6, 8])[0]
            conn.execute("INSERT INTO reviews VALUES (?,?,?,?,?)",
                         (rid, product_id, customer_id, rating, created.isoformat()))
            rid += 1

    conn.commit()
    counts = {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ["customers", "categories", "products", "orders", "order_items", "reviews"]}
    conn.close()
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/korean/database/shop/shop.sqlite")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    counts = build(Path(args.out), args.seed)
    print(counts, "->", args.out)


if __name__ == "__main__":
    main()
