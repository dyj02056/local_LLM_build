"""한국어 학습 데이터용 가상 DB 4개를 만든다 (도서관, 병원, 학원, 여행사).

평가용 쇼핑몰 DB(shop)와 겹치지 않도록 전자상거래 형태는 일부러 뺐다.
모든 DB는 중간 테이블을 거치는 긴 JOIN 경로를 갖는다.

    python scripts/build_korean_train_dbs.py
결과: data/korean_train/database/<db_id>/<db_id>.sqlite
"""

import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"]
GIVEN = ["태윤", "서아", "하람", "윤슬", "도현", "가온", "시온", "나래", "다온", "은호", "리안", "채율",
         "로운", "해솔", "지안", "온유", "새봄", "라온", "준혁", "수빈", "민서", "유나", "현서", "건호",
         "보람", "예솔", "한결", "이든", "다인", "주하"]


def names(rnd: random.Random, n: int) -> list[str]:
    out, seen = [], set()
    while len(out) < n:
        nm = rnd.choice(SURNAMES) + rnd.choice(GIVEN)
        if nm not in seen:
            seen.add(nm)
            out.append(nm)
    return out


def day(rnd: random.Random, start: date, end: date) -> str:
    return (start + timedelta(days=rnd.randrange((end - start).days + 1))).isoformat()


def build_library(conn, rnd):
    conn.executescript("""
    CREATE TABLE genres (genre_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
    CREATE TABLE authors (
        author_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        nationality TEXT NOT NULL      -- '한국', '일본', '미국', '영국', '프랑스'
    );
    CREATE TABLE books (
        book_id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        author_id INTEGER NOT NULL REFERENCES authors(author_id),
        genre_id INTEGER NOT NULL REFERENCES genres(genre_id),
        published_year INTEGER NOT NULL,
        pages INTEGER NOT NULL
    );
    CREATE TABLE members (
        member_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        gender TEXT NOT NULL,          -- 'M' 또는 'F'
        birth_year INTEGER NOT NULL,
        district TEXT NOT NULL,        -- 서울의 구 이름
        membership TEXT NOT NULL,      -- '일반', '우수', '평생'
        joined_at DATE NOT NULL
    );
    CREATE TABLE loans (
        loan_id INTEGER PRIMARY KEY,
        member_id INTEGER NOT NULL REFERENCES members(member_id),
        book_id INTEGER NOT NULL REFERENCES books(book_id),
        loan_date DATE NOT NULL,
        status TEXT NOT NULL           -- '반납', '대출중', '연체'
    );
    CREATE TABLE book_reviews (
        review_id INTEGER PRIMARY KEY,
        book_id INTEGER NOT NULL REFERENCES books(book_id),
        member_id INTEGER NOT NULL REFERENCES members(member_id),
        rating INTEGER NOT NULL        -- 1~5
    );
    """)
    genres = ["소설", "에세이", "역사", "과학", "경제", "자기계발", "만화", "여행"]
    conn.executemany("INSERT INTO genres VALUES (?,?)", list(enumerate(genres, 1)))
    nats = ["한국"] * 4 + ["일본", "미국", "영국", "프랑스"]
    authors = [(i, n, rnd.choice(nats)) for i, n in enumerate(names(rnd, 40), 1)]
    conn.executemany("INSERT INTO authors VALUES (?,?,?)", authors)
    adj = ["푸른", "고요한", "낯선", "작은", "오래된", "따뜻한", "멀리 있는", "잃어버린", "빛나는", "보이지 않는"]
    noun = ["바다", "정원", "도시", "편지", "기억", "계절", "지도", "숲", "기차", "섬", "하늘", "골목"]
    titles = rnd.sample([f"{a} {n}" for a in adj for n in noun], 120)
    books = [(i, t, rnd.randint(1, 40), rnd.randint(1, 8), rnd.randint(1998, 2025), rnd.randrange(120, 620, 4))
             for i, t in enumerate(titles, 1)]
    conn.executemany("INSERT INTO books VALUES (?,?,?,?,?,?)", books)
    districts = ["강남구", "마포구", "송파구", "노원구", "종로구", "관악구", "서초구", "은평구"]
    members = [(i, n, rnd.choice("MF"), rnd.randint(1950, 2010), rnd.choice(districts),
                rnd.choice(["일반"] * 6 + ["우수"] * 3 + ["평생"]), day(rnd, date(2019, 1, 1), date(2025, 6, 30)))
               for i, n in enumerate(names(rnd, 180), 1)]
    conn.executemany("INSERT INTO members VALUES (?,?,?,?,?,?,?)", members)
    w = [rnd.uniform(0.2, 3) for _ in books]
    loans = [(i, rnd.randint(1, 180), rnd.choices(books, w)[0][0], day(rnd, date(2024, 1, 1), date(2025, 12, 31)),
              rnd.choice(["반납"] * 8 + ["대출중"] * 2 + ["연체"])) for i in range(1, 901)]
    conn.executemany("INSERT INTO loans VALUES (?,?,?,?,?)", loans)
    reviews = [(i, l[2], l[1], rnd.choices([1, 2, 3, 4, 5], [1, 1, 3, 5, 6])[0])
               for i, l in enumerate([x for x in loans if rnd.random() < 0.35], 1)]
    conn.executemany("INSERT INTO book_reviews VALUES (?,?,?,?)", reviews)


def build_hospital(conn, rnd):
    conn.executescript("""
    CREATE TABLE departments (dept_id INTEGER PRIMARY KEY, name TEXT NOT NULL, floor INTEGER NOT NULL);
    CREATE TABLE doctors (
        doctor_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        dept_id INTEGER NOT NULL REFERENCES departments(dept_id),
        career_years INTEGER NOT NULL
    );
    CREATE TABLE patients (
        patient_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        gender TEXT NOT NULL,          -- 'M' 또는 'F'
        birth_year INTEGER NOT NULL,
        region TEXT NOT NULL,
        insurance TEXT NOT NULL        -- '건강보험', '의료급여', '비급여'
    );
    CREATE TABLE appointments (
        appt_id INTEGER PRIMARY KEY,
        patient_id INTEGER NOT NULL REFERENCES patients(patient_id),
        doctor_id INTEGER NOT NULL REFERENCES doctors(doctor_id),
        visit_date DATE NOT NULL,
        status TEXT NOT NULL,          -- '진료완료', '예약', '취소'
        fee INTEGER NOT NULL           -- 진료비 (원)
    );
    CREATE TABLE drugs (
        drug_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        maker TEXT NOT NULL,
        unit_price INTEGER NOT NULL    -- 1정(캡슐)당 가격 (원)
    );
    CREATE TABLE prescriptions (
        rx_id INTEGER PRIMARY KEY,
        appt_id INTEGER NOT NULL REFERENCES appointments(appt_id),
        drug_id INTEGER NOT NULL REFERENCES drugs(drug_id),
        days INTEGER NOT NULL,         -- 처방 일수
        daily_dose INTEGER NOT NULL    -- 하루 복용 횟수
    );
    """)
    depts = [("내과", 2), ("외과", 3), ("소아과", 2), ("정형외과", 4), ("피부과", 5), ("안과", 5), ("이비인후과", 3)]
    conn.executemany("INSERT INTO departments VALUES (?,?,?)", [(i, n, f) for i, (n, f) in enumerate(depts, 1)])
    conn.executemany("INSERT INTO doctors VALUES (?,?,?,?)",
                     [(i, n, rnd.randint(1, 7), rnd.randint(1, 30)) for i, n in enumerate(names(rnd, 28), 1)])
    regions = ["서울", "성남", "용인", "수원", "고양", "인천", "의정부"]
    conn.executemany("INSERT INTO patients VALUES (?,?,?,?,?,?)",
                     [(i, n, rnd.choice("MF"), rnd.randint(1940, 2022), rnd.choice(regions),
                       rnd.choice(["건강보험"] * 8 + ["의료급여", "비급여"])) for i, n in enumerate(names(rnd, 220), 1)])
    drugs = ["아세트아미노펜정", "이부프로펜정", "아목시실린캡슐", "세티리진정", "오메프라졸캡슐", "로라타딘정",
             "덱사메타손정", "메트포르민정", "암로디핀정", "레보플록사신정", "트라마돌캡슐", "판토프라졸정"]
    makers = ["한빛제약", "푸른약품", "새솔바이오", "온누리제약"]
    conn.executemany("INSERT INTO drugs VALUES (?,?,?,?)",
                     [(i, d, rnd.choice(makers), rnd.randrange(80, 900, 10)) for i, d in enumerate(drugs, 1)])
    appts = []
    for i in range(1, 801):
        st = rnd.choice(["진료완료"] * 7 + ["예약"] * 2 + ["취소"])
        appts.append((i, rnd.randint(1, 220), rnd.randint(1, 28), day(rnd, date(2025, 1, 1), date(2025, 12, 31)), st,
                      rnd.randrange(5000, 40000, 500)))
    conn.executemany("INSERT INTO appointments VALUES (?,?,?,?,?,?)", appts)
    rx, rid = [], 1
    for a in appts:
        if a[4] != "진료완료":
            continue
        for d in rnd.sample(range(1, 13), rnd.choice([0, 1, 1, 2, 3])):
            rx.append((rid, a[0], d, rnd.choice([3, 5, 7, 14, 30]), rnd.choice([1, 2, 3])))
            rid += 1
    conn.executemany("INSERT INTO prescriptions VALUES (?,?,?,?,?)", rx)


def build_academy(conn, rnd):
    conn.executescript("""
    CREATE TABLE subjects (subject_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
    CREATE TABLE teachers (
        teacher_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        subject_id INTEGER NOT NULL REFERENCES subjects(subject_id),
        hired_year INTEGER NOT NULL
    );
    CREATE TABLE courses (
        course_id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        subject_id INTEGER NOT NULL REFERENCES subjects(subject_id),
        teacher_id INTEGER NOT NULL REFERENCES teachers(teacher_id),
        level TEXT NOT NULL,           -- '기초', '중급', '심화'
        monthly_fee INTEGER NOT NULL,  -- 월 수강료 (원)
        weekday TEXT NOT NULL          -- '월', '화', '수', '목', '금', '토'
    );
    CREATE TABLE students (
        student_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        gender TEXT NOT NULL,          -- 'M' 또는 'F'
        school_grade TEXT NOT NULL,    -- '중1' ~ '고3'
        school_name TEXT NOT NULL
    );
    CREATE TABLE enrollments (
        enroll_id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(student_id),
        course_id INTEGER NOT NULL REFERENCES courses(course_id),
        start_date DATE NOT NULL,
        status TEXT NOT NULL           -- '수강중', '수료', '중도포기'
    );
    CREATE TABLE exams (
        exam_id INTEGER PRIMARY KEY,
        enroll_id INTEGER NOT NULL REFERENCES enrollments(enroll_id),
        exam_date DATE NOT NULL,
        score INTEGER NOT NULL         -- 0~100
    );
    """)
    subjects = ["수학", "영어", "국어", "과학", "코딩", "논술"]
    conn.executemany("INSERT INTO subjects VALUES (?,?)", list(enumerate(subjects, 1)))
    teachers = [(i, n, (i - 1) % 6 + 1, rnd.randint(2008, 2025)) for i, n in enumerate(names(rnd, 18), 1)]
    conn.executemany("INSERT INTO teachers VALUES (?,?,?,?)", teachers)
    courses, cid = [], 1
    for t in teachers:
        for lv in rnd.sample(["기초", "중급", "심화"], rnd.choice([1, 2, 2])):
            subj = subjects[t[2] - 1]
            courses.append((cid, f"{subj} {lv}반 {cid}", t[2], t[0], lv, rnd.randrange(150000, 460000, 10000),
                            rnd.choice(list("월화수목금토"))))
            cid += 1
    conn.executemany("INSERT INTO courses VALUES (?,?,?,?,?,?,?)", courses)
    schools = ["한빛중", "새솔중", "푸른고", "온누리고", "다솜고"]
    grades = ["중1", "중2", "중3", "고1", "고2", "고3"]
    students = []
    for i, n in enumerate(names(rnd, 200), 1):
        g = rnd.choice(grades)
        sch = rnd.choice([s for s in schools if s.endswith(g[0])])
        students.append((i, n, rnd.choice("MF"), g, sch))
    conn.executemany("INSERT INTO students VALUES (?,?,?,?,?)", students)
    enrolls = [(i, rnd.randint(1, 200), rnd.randint(1, len(courses)), day(rnd, date(2024, 3, 1), date(2025, 11, 30)),
                rnd.choice(["수강중"] * 4 + ["수료"] * 4 + ["중도포기"])) for i in range(1, 701)]
    conn.executemany("INSERT INTO enrollments VALUES (?,?,?,?,?)", enrolls)
    exams, eid = [], 1
    for e in enrolls:
        for _ in range(rnd.choice([0, 1, 2])):
            exams.append((eid, e[0], day(rnd, date.fromisoformat(e[3]), date(2025, 12, 31)), rnd.randint(35, 100)))
            eid += 1
    conn.executemany("INSERT INTO exams VALUES (?,?,?,?)", exams)


def build_travel(conn, rnd):
    conn.executescript("""
    CREATE TABLE regions (
        region_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        country TEXT NOT NULL          -- '한국', '일본', '베트남', '태국', '프랑스'
    );
    CREATE TABLE hotels (
        hotel_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        region_id INTEGER NOT NULL REFERENCES regions(region_id),
        stars INTEGER NOT NULL         -- 1~5성급
    );
    CREATE TABLE packages (
        package_id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        hotel_id INTEGER NOT NULL REFERENCES hotels(hotel_id),
        nights INTEGER NOT NULL,
        price INTEGER NOT NULL,        -- 1인 가격 (원)
        season TEXT NOT NULL           -- '봄', '여름', '가을', '겨울'
    );
    CREATE TABLE travelers (
        traveler_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        gender TEXT NOT NULL,          -- 'M' 또는 'F'
        birth_year INTEGER NOT NULL,
        home_city TEXT NOT NULL
    );
    CREATE TABLE bookings (
        booking_id INTEGER PRIMARY KEY,
        traveler_id INTEGER NOT NULL REFERENCES travelers(traveler_id),
        package_id INTEGER NOT NULL REFERENCES packages(package_id),
        booking_date DATE NOT NULL,
        people INTEGER NOT NULL,       -- 예약 인원
        status TEXT NOT NULL           -- '여행완료', '확정', '취소'
    );
    CREATE TABLE trip_reviews (
        review_id INTEGER PRIMARY KEY,
        booking_id INTEGER NOT NULL REFERENCES bookings(booking_id),
        rating INTEGER NOT NULL        -- 1~5
    );
    """)
    regions = [("제주", "한국"), ("부산", "한국"), ("강릉", "한국"), ("오사카", "일본"), ("후쿠오카", "일본"),
               ("다낭", "베트남"), ("방콕", "태국"), ("파리", "프랑스")]
    conn.executemany("INSERT INTO regions VALUES (?,?,?)", [(i, n, c) for i, (n, c) in enumerate(regions, 1)])
    hn = ["바람", "노을", "파도", "별빛", "솔숲", "물결", "햇살", "달빛"]
    hotels = [(i, f"{rnd.choice(hn)}호텔 {i}호점", (i - 1) % 8 + 1, rnd.randint(2, 5)) for i in range(1, 25)]
    conn.executemany("INSERT INTO hotels VALUES (?,?,?,?)", hotels)
    packages = []
    for i in range(1, 61):
        h = rnd.choice(hotels)
        region = regions[h[2] - 1][0]
        nights = rnd.choice([2, 3, 4, 5])
        packages.append((i, f"{region} {nights}박 패키지 {i}", h[0], nights,
                         rnd.randrange(250000, 2400000, 10000), rnd.choice(["봄", "여름", "가을", "겨울"])))
    conn.executemany("INSERT INTO packages VALUES (?,?,?,?,?,?)", packages)
    cities = ["서울", "부산", "대구", "대전", "광주", "인천"]
    conn.executemany("INSERT INTO travelers VALUES (?,?,?,?,?)",
                     [(i, n, rnd.choice("MF"), rnd.randint(1955, 2005), rnd.choice(cities))
                      for i, n in enumerate(names(rnd, 200), 1)])
    bookings = [(i, rnd.randint(1, 200), rnd.randint(1, 60), day(rnd, date(2024, 6, 1), date(2025, 12, 31)),
                 rnd.choices([1, 2, 3, 4], [3, 5, 1, 1])[0], rnd.choice(["여행완료"] * 6 + ["확정"] * 2 + ["취소"]))
                for i in range(1, 701)]
    conn.executemany("INSERT INTO bookings VALUES (?,?,?,?,?,?)", bookings)
    reviews = [(i, b[0], rnd.choices([1, 2, 3, 4, 5], [1, 1, 2, 5, 6])[0])
               for i, b in enumerate([b for b in bookings if b[5] == "여행완료" and rnd.random() < 0.5], 1)]
    conn.executemany("INSERT INTO trip_reviews VALUES (?,?,?)", reviews)


BUILDERS = {"library": build_library, "hospital": build_hospital, "academy": build_academy, "travel": build_travel}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/korean_train/database")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    for i, (db_id, build) in enumerate(BUILDERS.items()):
        path = Path(args.root) / db_id / f"{db_id}.sqlite"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.unlink(missing_ok=True)
        conn = sqlite3.connect(path)
        build(conn, random.Random(args.seed * 100 + i))
        conn.commit()
        tables = [t for (t,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        print(db_id, {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in tables})
        conn.close()


if __name__ == "__main__":
    main()
