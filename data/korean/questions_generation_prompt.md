당신은 한국 온라인 쇼핑몰의 데이터 분석가입니다. 사내에 도입할 "한국어 질문 → SQL" AI를 평가하려고 합니다.
아래 SQLite 데이터베이스에 대해, 실제 직원이 물어볼 법한 한국어 질문 30개와 각 질문의 정답 SQL을 만들어 주세요.

## 데이터베이스 스키마 (SQLite)

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
    price INTEGER NOT NULL,        -- 현재 판매가 (원)
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

## 실제로 들어 있는 값
- 고객 200명, 상품 41개, 주문 800건, 주문 상품 1,171줄, 리뷰 380개
- 도시: 광주, 대구, 대전, 부산, 서울, 수원, 인천, 제주
- 카테고리: 전자제품, 의류, 식품, 도서, 뷰티, 스포츠, 가구, 완구
- 브랜드: 글밭, 꽃잎, 나무공방, 놀이터, 달리기, 데일리웨어, 든든, 들녘, 맑은피부, 목장, 산마루, 소리샘, 아침커피, 어반핏, 역사책방, 운동가, 충전왕, 코딩출판, 타건, 편한집, 포근, 화면나라
- 상품 예: 무선 이어폰, 27인치 모니터, 스마트워치, 청바지, 경량 패딩, 제주 감귤 5kg, 파이썬 첫걸음, 수분 크림, 러닝화, 원목 책상, 보드게임
- 주문 날짜: 2025-01-01 ~ 2025-12-31 / 가입일: 2023-01-06 ~ 2025-06-20 / 출생연도: 1965 ~ 2005
- 주문 1건에는 여러 상품이 담길 수 있고, 상품별 수량과 주문 당시 가격은 order_items에만 있습니다.

## 질문 작성 규칙
1. 실제 쇼핑몰 직원(MD, 마케터, CS 담당, 팀장)이 메신저나 회의에서 묻는 말투로 쓰세요. 반말, 존댓말, 짧은 메신저체를 섞고, 같은 뜻의 다른 표현(매출/판매액/구매 금액, 고객/회원/손님, 주문/구매)을 골고루 쓰세요.
2. 질문에 영어 테이블명이나 컬럼명(order_items, unit_price 등)을 쓰지 마세요.
3. 정답이 하나로 정해지도록 쓰세요.
   - 취소된 주문을 포함하는지 빼는지 질문에 밝히세요.
   - "매출"은 무엇으로 계산하는지(예: 수량 × 주문 당시 가격) 질문에 밝히세요.
   - 여러 값을 묻는 질문은 무엇을 보여 줄지 분명히 쓰세요 (예: "이름과 주문 건수").
   - 순서가 중요한 경우에만 정렬을 요청하세요 (예: "많은 순으로").
   - "최근", "지난달" 같은 표현은 기준일을 2025년 12월 31일로 질문 안에 밝히세요.
4. 스키마에 없는 정보(배송비, 쿠폰, 장바구니, 재방문율 등)는 묻지 마세요.
5. 난이도 구성 (총 30개):
   - 쉬움 8개: 테이블 1개만 써도 되는 질문
   - 보통 10개: JOIN 1개 또는 GROUP BY가 필요한 질문
   - 어려움 12개: JOIN 2개 이상이 필요한 질문. 그중 최소 8개는 고객/카테고리/브랜드와 수량·금액을 함께 묻는 등 order_items를 거쳐 테이블 3~5개를 이어야 하는 질문으로 하고, 나머지에는 서브쿼리, INTERSECT/EXCEPT, HAVING을 섞으세요.

## 정답 SQL 작성 규칙
- SQLite 문법, SELECT 문 하나만 쓰세요.
- SELECT하는 컬럼의 순서는 질문에서 언급한 순서를 따르세요.
- 질문이 순서를 요구할 때만 ORDER BY를 쓰고, "상위 N개"를 물을 때만 LIMIT을 쓰세요.
- 값은 위 목록의 한국어 값을 정확히 쓰세요 (예: status = '취소').
- 결과값을 직접 계산할 필요는 없습니다. SQL만 정확하면 됩니다.

## 출력 형식
설명 없이 아래 형식의 JSON 배열만 출력하세요.
note에는 질문이 애매할 수 있는 부분과 그것을 어떻게 정했는지 한 줄로 적으세요 (없으면 빈 문자열).

[
  {"id": 1, "level": "쉬움", "question": "...", "query": "SELECT ...", "note": "..."},
  ...
]