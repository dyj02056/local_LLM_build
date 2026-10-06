"""v3 학습 데이터: JOIN이 필요한 질문과 필요 없는 질문의 균형을 맞춘다.

    python scripts/build_korean_train_dbs.py
    python scripts/gen_korean_train_v3.py   # -> data/korean_train/train_ko_v3.jsonl
    python scripts/make_train_v2.py --korean data/korean_train/train_ko_v3.jsonl --out data/sft/train_v3.jsonl

v2는 학습 데이터의 62%가 JOIN 2개 이상이라 "일단 JOIN을 많이 하는" 버릇이 생겼다
(외부 질문에서 JOIN 0~1개 문항이 새로 맞음 3 / 새로 틀림 9). v3은
- v2 템플릿에 한 테이블로 답하는 질문 위주의 새 템플릿을 더하고 (합계 120개 이상),
- 말투는 비슷한데 JOIN 필요 여부만 다른 대조 쌍을 넣고 (예: 장르별 책 권수 ↔ 출간 연도별 책 권수),
- JOIN 수 비율을 외부 질문 분포(0개 50%, 1개 15%, 2개 이상 35%)에 맞춰 뽑는다.
한국어 예시 수는 v2(940개)와 비슷하게 두어, 바뀐 것이 JOIN 비율뿐이 되게 한다.
평가용 쇼핑몰 DB(shop)와 평가 질문(직접 만든 100개, 외부 118개)은 쓰지 않는다.
"""

import argparse
import json
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from gen_korean_train import MONTHS, TEMPLATES, A, H, L, T, V, ambiguous, combos, join_count
from text2sql.prompt import build_messages
from text2sql.schema import db_path_for, get_schema

YEARS = [{"y": y} for y in range(2019, 2026)]

# 대조 쌍은 "대조:" 주석으로 표시한다. 짝이 되는 JOIN 템플릿은 v2(TEMPLATES)나 바로 옆에 있다.
NEW_TEMPLATES = [
    # ---------------- 도서관 ----------------
    T(L, ["회원은 모두 몇 명이야?", "등록된 회원 수를 알려 줘."], "SELECT count(*) FROM members"),
    T(L, ["책은 모두 몇 권 있어?", "도서관에 있는 책 권수를 알려 줘."], "SELECT count(*) FROM books"),
    # 대조: 장르별 책 권수(JOIN 1개) ↔ 출간 연도별 책 권수(books만)
    T(L, ["출간 연도별 책 권수를 알려 줘.", "연도마다 나온 책이 몇 권씩인지 보여 줘."],
      "SELECT published_year, count(*) FROM books GROUP BY published_year"),
    # 대조: 국적이 X인 작가의 책 수(JOIN 1개) ↔ 국적별 작가 수(authors만)
    T(L, ["국적별 작가 수를 알려 줘.", "작가가 나라마다 몇 명씩 있어?"],
      "SELECT nationality, count(*) FROM authors GROUP BY nationality"),
    T(L, ["회원 등급별 회원 수를 알려 줘.", "등급마다 회원이 몇 명씩이야?"],
      "SELECT membership, count(*) FROM members GROUP BY membership"),
    T(L, ["구별 회원 수를 많은 순으로 보여 줘.", "회원이 사는 구마다 몇 명인지 많은 순으로 알려 줘."],
      "SELECT district, count(*) FROM members GROUP BY district ORDER BY count(*) DESC"),
    T(L, ["{year}년에 가입한 회원은 몇 명이야?", "{year}년 가입 회원 수를 알려 줘."],
      "SELECT count(*) FROM members WHERE joined_at BETWEEN '{year}-01-01' AND '{year}-12-31'",
      {"_": [{"year": y} for y in range(2019, 2026)]}),
    T(L, ["{n}쪽 이상인 책 제목과 쪽수를 보여 줘.", "쪽수가 {n}쪽을 넘는 책은 뭐가 있어? 제목이랑 쪽수 알려 줘."],
      "SELECT title, pages FROM books WHERE pages >= {n}", {"_": [{"n": n} for n in (450, 500, 550, 600)]}),
    T(L, ["{district}에 사는 여성 회원 이름을 알려 줘.", "{district} 거주 여자 회원은 누구야?"],
      "SELECT name FROM members WHERE district = '{district}' AND gender = 'F'",
      {"district": "SELECT DISTINCT district FROM members"}),
    T(L, ["{ms} 등급 회원의 이름과 가입일을 보여 줘."],
      "SELECT name, joined_at FROM members WHERE membership = '{ms}'", {"ms": "SELECT DISTINCT membership FROM members"}),
    T(L, ["책의 평균 쪽수는 얼마야?", "책들은 평균 몇 쪽이야?"], "SELECT avg(pages) FROM books"),
    T(L, ["{year}년 이후에 나온 책은 몇 권이야?"],
      "SELECT count(*) FROM books WHERE published_year >= {year}", {"_": [{"year": y} for y in (2010, 2015, 2020, 2023)]}),
    T(L, ["평점이 {r}점인 리뷰는 몇 개야?", "별점 {r}점짜리 리뷰 개수를 알려 줘."],
      "SELECT count(*) FROM book_reviews WHERE rating = {r}", {"_": [{"r": r} for r in range(1, 6)]}),
    T(L, ["책을 한 번이라도 빌린 회원은 몇 명이야?", "대출 기록이 있는 회원 수를 중복 없이 알려 줘."],
      "SELECT count(DISTINCT member_id) FROM loans"),
    T(L, ["대출을 {n}번 이상 한 회원 ID와 대출 건수를 보여 줘."],
      "SELECT member_id, count(*) FROM loans GROUP BY member_id HAVING count(*) >= {n}", {"_": [{"n": n} for n in (8, 9, 10)]}),
    T(L, ["2025년 월별 대출 건수를 알려 줘. 월은 '2025-01'처럼 보여 줘."],
      "SELECT strftime('%Y-%m', loan_date), count(*) FROM loans WHERE loan_date BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY strftime('%Y-%m', loan_date)"),
    T(L, ["리뷰를 한 번도 쓰지 않은 회원 이름을 알려 줘."],
      "SELECT name FROM members WHERE member_id NOT IN (SELECT member_id FROM book_reviews)"),
    T(L, ["책을 빌린 적도 있고 리뷰도 쓴 회원 ID를 알려 줘."],
      "SELECT member_id FROM loans INTERSECT SELECT member_id FROM book_reviews"),
    # 1개 JOIN: 이름을 붙여 집계
    T(L, ["작가별 책 수를 작가 이름과 함께 많은 순으로 보여 줘.", "작가마다 책을 몇 권 썼는지 이름이랑 같이 많은 순으로 알려 줘."],
      "SELECT T2.name, count(*) FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id GROUP BY T2.author_id ORDER BY count(*) DESC"),
    T(L, ["평균 평점이 {r}점 이상인 책 제목과 평균 평점을 보여 줘."],
      "SELECT T2.title, avg(T1.rating) FROM book_reviews AS T1 JOIN books AS T2 ON T1.book_id = T2.book_id GROUP BY T1.book_id HAVING avg(T1.rating) >= {r}",
      {"_": [{"r": 4.5}, {"r": 4.8}]}),
    T(L, ["{genre} 장르 책 제목과 출간 연도를 알려 줘."],
      "SELECT T1.title, T1.published_year FROM books AS T1 JOIN genres AS T2 ON T1.genre_id = T2.genre_id WHERE T2.name = '{genre}'",
      {"genre": "SELECT name FROM genres"}),

    # ---------------- 병원 ----------------
    T(H, ["환자는 모두 몇 명이야?", "등록된 환자 수를 알려 줘."], "SELECT count(*) FROM patients"),
    # 대조: 제약사별 처방 건수(JOIN 1개) ↔ 제약사별 약 개수(drugs만)
    T(H, ["제약사별 약 개수를 알려 줘.", "제약회사마다 약이 몇 개씩 있어?"], "SELECT maker, count(*) FROM drugs GROUP BY maker"),
    T(H, ["제약사별 약 평균 가격을 비싼 순으로 보여 줘."],
      "SELECT maker, avg(unit_price) FROM drugs GROUP BY maker ORDER BY avg(unit_price) DESC"),
    # 대조: 진료과별 의사 수(JOIN 1개) ↔ 층별 진료과 수(departments만)
    T(H, ["층별 진료과 수를 알려 줘.", "몇 층에 진료과가 몇 개씩 있어?"], "SELECT floor, count(*) FROM departments GROUP BY floor"),
    T(H, ["지역별 환자 수를 많은 순으로 알려 줘.", "환자가 사는 지역마다 몇 명인지 많은 순으로 보여 줘."],
      "SELECT region, count(*) FROM patients GROUP BY region ORDER BY count(*) DESC"),
    T(H, ["진료 상태별 건수를 알려 줘.", "진료가 상태마다 몇 건씩이야?"], "SELECT status, count(*) FROM appointments GROUP BY status"),
    T(H, ["경력이 {n}년 이상인 의사 이름과 경력 연수를 보여 줘.", "경력 {n}년 넘은 의사는 누구야? 경력도 알려 줘."],
      "SELECT name, career_years FROM doctors WHERE career_years >= {n}", {"_": [{"n": n} for n in (15, 20, 25)]}),
    T(H, ["{maker}에서 만든 약 이름과 가격을 알려 줘."],
      "SELECT name, unit_price FROM drugs WHERE maker = '{maker}'", {"maker": "SELECT DISTINCT maker FROM drugs"}),
    T(H, ["{region}에 사는 {ins} 환자는 몇 명이야?"],
      "SELECT count(*) FROM patients WHERE region = '{region}' AND insurance = '{ins}'",
      {"region": "SELECT DISTINCT region FROM patients", "ins": "SELECT DISTINCT insurance FROM patients"}),
    T(H, ["{year}년 이후 태어난 환자 이름과 출생 연도를 보여 줘."],
      "SELECT name, birth_year FROM patients WHERE birth_year >= {year}", {"_": [{"year": y} for y in (2015, 2018, 2020)]}),
    T(H, ["진료완료된 진료의 평균 진료비는 얼마야?", "진료를 마친 건들의 진료비 평균을 구해 줘."],
      "SELECT avg(fee) FROM appointments WHERE status = '진료완료'"),
    T(H, ["가장 비싼 약의 이름과 가격은?", "1정 가격이 제일 높은 약이 뭐야?"],
      "SELECT name, unit_price FROM drugs ORDER BY unit_price DESC LIMIT 1", rank="SELECT unit_price FROM drugs ORDER BY unit_price DESC"),
    T(H, ["2025년 월별 진료 건수를 알려 줘. 월은 '2025-01'처럼 보여 줘."],
      "SELECT strftime('%Y-%m', visit_date), count(*) FROM appointments GROUP BY strftime('%Y-%m', visit_date)"),
    T(H, ["진료를 받은 적 있는 환자는 중복 없이 몇 명이야?"], "SELECT count(DISTINCT patient_id) FROM appointments"),
    T(H, ["처방 일수별 처방 건수를 알려 줘.", "며칠치 처방이 각각 몇 건이야?"], "SELECT days, count(*) FROM prescriptions GROUP BY days"),
    T(H, ["진료를 {n}번 이상 받은 환자 ID와 진료 횟수를 보여 줘."],
      "SELECT patient_id, count(*) FROM appointments GROUP BY patient_id HAVING count(*) >= {n}", {"_": [{"n": n} for n in (7, 8, 9)]}),
    # 1개 JOIN
    T(H, ["의사별 진료 건수를 의사 이름과 함께 많은 순으로 보여 줘."],
      "SELECT T2.name, count(*) FROM appointments AS T1 JOIN doctors AS T2 ON T1.doctor_id = T2.doctor_id GROUP BY T2.doctor_id ORDER BY count(*) DESC"),
    T(H, ["약별 처방 건수를 약 이름과 함께 보여 줘.", "약마다 몇 번 처방됐는지 이름이랑 알려 줘."],
      "SELECT T2.name, count(*) FROM prescriptions AS T1 JOIN drugs AS T2 ON T1.drug_id = T2.drug_id GROUP BY T2.drug_id"),
    T(H, ["{patient} 환자의 진료 날짜와 진료비를 알려 줘."],
      "SELECT T2.visit_date, T2.fee FROM patients AS T1 JOIN appointments AS T2 ON T1.patient_id = T2.patient_id WHERE T1.name = '{patient}'",
      {"patient": "SELECT DISTINCT T1.name FROM patients AS T1 JOIN appointments AS T2 ON T1.patient_id = T2.patient_id"}),

    # ---------------- 학원 ----------------
    T(A, ["학생은 모두 몇 명이야?", "등록된 학생 수를 알려 줘."], "SELECT count(*) FROM students"),
    # 대조: 과목별 강좌 수(JOIN 1개) ↔ 수준별 강좌 수(courses만)
    T(A, ["수준별 강좌 수를 알려 줘.", "기초, 중급, 심화 강좌가 각각 몇 개야?"], "SELECT level, count(*) FROM courses GROUP BY level"),
    T(A, ["요일별 강좌 수를 알려 줘.", "요일마다 강좌가 몇 개씩 열려?"], "SELECT weekday, count(*) FROM courses GROUP BY weekday"),
    # 대조: 과목별 평균 시험 점수(JOIN 3개) ↔ 수준별 평균 월 수강료(courses만)
    T(A, ["수준별 평균 월 수강료를 비싼 순으로 보여 줘."],
      "SELECT level, avg(monthly_fee) FROM courses GROUP BY level ORDER BY avg(monthly_fee) DESC"),
    T(A, ["학년별 학생 수를 알려 줘.", "학년마다 학생이 몇 명씩 있어?"], "SELECT school_grade, count(*) FROM students GROUP BY school_grade"),
    T(A, ["학교별 학생 수를 많은 순으로 알려 줘."], "SELECT school_name, count(*) FROM students GROUP BY school_name ORDER BY count(*) DESC"),
    T(A, ["{year}년 이후에 채용된 선생님 이름을 알려 줘.", "{year}년부터 들어온 선생님은 누구야?"],
      "SELECT name FROM teachers WHERE hired_year >= {year}", {"_": [{"year": y} for y in (2015, 2018, 2020, 2022)]}),
    T(A, ["월 수강료가 {n}원 이상인 강좌 제목과 수강료를 보여 줘."],
      "SELECT title, monthly_fee FROM courses WHERE monthly_fee >= {n}", {"_": [{"n": n} for n in (300000, 350000, 400000)]}),
    T(A, ["{wd}요일 {level} 강좌 제목을 알려 줘."],
      "SELECT title FROM courses WHERE weekday = '{wd}' AND level = '{level}'",
      {"wd": "SELECT DISTINCT weekday FROM courses", "level": "SELECT DISTINCT level FROM courses"}),
    T(A, ["{school} {grade} 학생 이름을 알려 줘."],
      "SELECT name FROM students WHERE school_name = '{school}' AND school_grade = '{grade}'",
      {"school": "SELECT DISTINCT school_name FROM students", "grade": "SELECT DISTINCT school_grade FROM students"}),
    T(A, ["시험 점수가 {n}점 이상인 시험은 몇 개야?"],
      "SELECT count(*) FROM exams WHERE score >= {n}", {"_": [{"n": n} for n in (80, 90, 95)]}),
    T(A, ["시험 평균 점수는 몇 점이야?", "전체 시험 점수 평균을 구해 줘."], "SELECT avg(score) FROM exams"),
    T(A, ["강좌에 등록한 적 있는 학생은 중복 없이 몇 명이야?"], "SELECT count(DISTINCT student_id) FROM enrollments"),
    T(A, ["중도포기한 등록 건의 학생 ID와 시작일을 보여 줘."], "SELECT student_id, start_date FROM enrollments WHERE status = '중도포기'"),
    T(A, ["등록을 {n}번 이상 한 학생 ID와 등록 건수를 보여 줘."],
      "SELECT student_id, count(*) FROM enrollments GROUP BY student_id HAVING count(*) >= {n}", {"_": [{"n": n} for n in (6, 7)]}),
    T(A, ["강좌에 한 번도 등록하지 않은 학생 이름은?"],
      "SELECT name FROM students WHERE student_id NOT IN (SELECT student_id FROM enrollments)"),
    # 1개 JOIN
    T(A, ["선생님별 강좌 수를 선생님 이름과 함께 많은 순으로 보여 줘."],
      "SELECT T2.name, count(*) FROM courses AS T1 JOIN teachers AS T2 ON T1.teacher_id = T2.teacher_id GROUP BY T2.teacher_id ORDER BY count(*) DESC"),
    T(A, ["강좌별 등록 학생 수를 강좌 제목과 함께 보여 줘."],
      "SELECT T2.title, count(*) FROM enrollments AS T1 JOIN courses AS T2 ON T1.course_id = T2.course_id GROUP BY T2.course_id"),
    T(A, ["{subject} 과목 강좌의 평균 월 수강료는?"],
      "SELECT avg(T1.monthly_fee) FROM courses AS T1 JOIN subjects AS T2 ON T1.subject_id = T2.subject_id WHERE T2.name = '{subject}'",
      {"subject": "SELECT name FROM subjects"}),

    # ---------------- 여행사 ----------------
    T(V, ["여행객은 모두 몇 명이야?", "등록된 고객 수를 알려 줘."], "SELECT count(*) FROM travelers"),
    # 대조: 지역별 호텔 수(JOIN 1개) ↔ 성급별 호텔 수(hotels만)
    T(V, ["성급별 호텔 수를 알려 줘.", "몇 성급 호텔이 각각 몇 개야?"], "SELECT stars, count(*) FROM hotels GROUP BY stars"),
    # 대조: 지역 패키지 평균 가격(JOIN 2개) ↔ 시즌별 패키지 평균 가격(packages만)
    T(V, ["시즌별 패키지 평균 가격을 알려 줘.", "계절마다 패키지가 평균 얼마야?"], "SELECT season, avg(price) FROM packages GROUP BY season"),
    T(V, ["시즌별 패키지 수를 알려 줘."], "SELECT season, count(*) FROM packages GROUP BY season"),
    T(V, ["숙박 일수별 패키지 수를 알려 줘.", "몇 박짜리 패키지가 각각 몇 개야?"], "SELECT nights, count(*) FROM packages GROUP BY nights"),
    T(V, ["국가별 지역 수를 알려 줘.", "나라마다 여행 지역이 몇 곳씩이야?"], "SELECT country, count(*) FROM regions GROUP BY country"),
    T(V, ["출신 도시별 여행객 수를 많은 순으로 보여 줘."],
      "SELECT home_city, count(*) FROM travelers GROUP BY home_city ORDER BY count(*) DESC"),
    T(V, ["{nights}박 패키지 제목과 가격을 알려 줘."],
      "SELECT title, price FROM packages WHERE nights = {nights}", {"nights": "SELECT DISTINCT nights FROM packages"}),
    T(V, ["가격이 {n}원 이하인 패키지는 몇 개야?", "{n}원 이하 패키지 개수를 알려 줘."],
      "SELECT count(*) FROM packages WHERE price <= {n}", {"_": [{"n": n} for n in (500000, 800000, 1000000)]}),
    T(V, ["{city}에 사는 남성 여행객 이름을 알려 줘."],
      "SELECT name FROM travelers WHERE home_city = '{city}' AND gender = 'M'", {"city": "SELECT DISTINCT home_city FROM travelers"}),
    T(V, ["{stars}성급 호텔 이름을 알려 줘."], "SELECT name FROM hotels WHERE stars = {stars}", {"stars": "SELECT DISTINCT stars FROM hotels"}),
    T(V, ["취소되지 않은 예약의 평균 인원은?", "취소를 빼고 예약 1건당 평균 몇 명이야?"], "SELECT avg(people) FROM bookings WHERE status != '취소'"),
    T(V, ["2025년 월별 예약 건수를 알려 줘. 월은 '2025-01'처럼 보여 줘."],
      "SELECT strftime('%Y-%m', booking_date), count(*) FROM bookings WHERE booking_date BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY strftime('%Y-%m', booking_date)"),
    T(V, ["예약을 한 번이라도 한 여행객은 중복 없이 몇 명이야?"], "SELECT count(DISTINCT traveler_id) FROM bookings"),
    T(V, ["평점이 {r}점인 여행 후기는 몇 개야?"], "SELECT count(*) FROM trip_reviews WHERE rating = {r}", {"_": [{"r": r} for r in range(1, 6)]}),
    T(V, ["예약을 {n}번 이상 한 여행객 ID와 예약 건수를 보여 줘."],
      "SELECT traveler_id, count(*) FROM bookings GROUP BY traveler_id HAVING count(*) >= {n}", {"_": [{"n": n} for n in (6, 7)]}),
    T(V, ["한 번도 예약하지 않은 여행객 이름은?"],
      "SELECT name FROM travelers WHERE traveler_id NOT IN (SELECT traveler_id FROM bookings)"),
    # 1개 JOIN
    T(V, ["{region} 호텔 이름과 성급을 알려 줘."],
      "SELECT T1.name, T1.stars FROM hotels AS T1 JOIN regions AS T2 ON T1.region_id = T2.region_id WHERE T2.name = '{region}'",
      {"region": "SELECT name FROM regions"}),
    T(V, ["패키지별 예약 건수를 패키지 제목과 함께 많은 순으로 보여 줘."],
      "SELECT T2.title, count(*) FROM bookings AS T1 JOIN packages AS T2 ON T1.package_id = T2.package_id GROUP BY T2.package_id ORDER BY count(*) DESC"),
    T(V, ["{traveler} 고객의 예약 날짜와 인원을 알려 줘."],
      "SELECT T2.booking_date, T2.people FROM travelers AS T1 JOIN bookings AS T2 ON T1.traveler_id = T2.traveler_id WHERE T1.name = '{traveler}'",
      {"traveler": "SELECT DISTINCT T1.name FROM travelers AS T1 JOIN bookings AS T2 ON T1.traveler_id = T2.traveler_id"}),

    # ---------------- 한 테이블 조건 조회 (값을 바꿔 가며 여러 개) ----------------
    T(L, ["{y}년생 회원은 몇 명이야?", "{y}년에 태어난 회원 수를 알려 줘."],
      "SELECT count(*) FROM members WHERE birth_year = {y}", {"y": "SELECT DISTINCT birth_year FROM members"}),
    T(L, ["{nat} 작가 이름을 알려 줘.", "국적이 {nat}인 작가는 누구야?"],
      "SELECT name FROM authors WHERE nationality = '{nat}'", {"nat": "SELECT DISTINCT nationality FROM authors"}),
    T(L, ["{status} 상태인 대출은 몇 건이야?", "대출 중 {status}인 건수를 알려 줘."],
      "SELECT count(*) FROM loans WHERE status = '{status}'", {"status": "SELECT DISTINCT status FROM loans"}),
    T(L, ["{district}에 사는 {ms} 등급 회원은 몇 명이야?"],
      "SELECT count(*) FROM members WHERE district = '{district}' AND membership = '{ms}'",
      {"district": "SELECT DISTINCT district FROM members", "ms": "SELECT DISTINCT membership FROM members"}),
    T(H, ["{y}년생 환자는 몇 명이야?", "{y}년에 태어난 환자 수를 알려 줘."],
      "SELECT count(*) FROM patients WHERE birth_year = {y}", {"y": "SELECT DISTINCT birth_year FROM patients"}),
    T(H, ["{floor}층에 있는 진료과 이름을 알려 줘.", "{floor}층에는 어떤 과가 있어?"],
      "SELECT name FROM departments WHERE floor = {floor}", {"floor": "SELECT DISTINCT floor FROM departments"}),
    T(H, ["{region} 환자 이름과 출생 연도를 보여 줘."],
      "SELECT name, birth_year FROM patients WHERE region = '{region}'", {"region": "SELECT DISTINCT region FROM patients"}),
    T(H, ["진료비가 {n}원 이상인 진료는 몇 건이야?", "{n}원 넘게 나온 진료 건수를 알려 줘."],
      "SELECT count(*) FROM appointments WHERE fee >= {n}", {"_": [{"n": n} for n in (20000, 25000, 30000, 35000)]}),
    T(H, ["{status} 상태 진료의 진료비 합계는?"],
      "SELECT sum(fee) FROM appointments WHERE status = '{status}'", {"status": "SELECT DISTINCT status FROM appointments"}),
    T(A, ["{level} 강좌 제목과 요일을 알려 줘.", "{level} 수업은 뭐가 있고 무슨 요일이야?"],
      "SELECT title, weekday FROM courses WHERE level = '{level}'", {"level": "SELECT DISTINCT level FROM courses"}),
    T(A, ["{grade} 여학생 이름을 알려 줘.", "학년이 {grade}인 여자 학생은 누구야?"],
      "SELECT name FROM students WHERE school_grade = '{grade}' AND gender = 'F'", {"grade": "SELECT DISTINCT school_grade FROM students"}),
    T(A, ["{wd}요일에 열리는 강좌는 몇 개야?"],
      "SELECT count(*) FROM courses WHERE weekday = '{wd}'", {"wd": "SELECT DISTINCT weekday FROM courses"}),
    T(A, ["등록 상태가 {status}인 건수를 알려 줘."],
      "SELECT count(*) FROM enrollments WHERE status = '{status}'", {"status": "SELECT DISTINCT status FROM enrollments"}),
    T(A, ["{year}년에 채용된 선생님은 몇 명이야?"],
      "SELECT count(*) FROM teachers WHERE hired_year = {year}", {"year": "SELECT DISTINCT hired_year FROM teachers"}),
    T(V, ["{y}년생 여행객은 몇 명이야?", "{y}년에 태어난 고객 수를 알려 줘."],
      "SELECT count(*) FROM travelers WHERE birth_year = {y}", {"y": "SELECT DISTINCT birth_year FROM travelers"}),
    T(V, ["{country} 여행 지역 이름을 알려 줘.", "{country}에는 어떤 여행지가 있어?"],
      "SELECT name FROM regions WHERE country = '{country}'", {"country": "SELECT DISTINCT country FROM regions"}),
    T(V, ["예약 상태가 {status}인 건은 몇 건이야?"],
      "SELECT count(*) FROM bookings WHERE status = '{status}'", {"status": "SELECT DISTINCT status FROM bookings"}),
    T(V, ["{season} 패키지 중 가장 싼 상품의 제목과 가격은?"],
      "SELECT title, price FROM packages WHERE season = '{season}' ORDER BY price LIMIT 1",
      {"season": "SELECT DISTINCT season FROM packages"},
      rank="SELECT price FROM packages WHERE season = '{season}' ORDER BY price"),
    T(V, ["{city} 출신 여행객 이름과 출생 연도를 보여 줘."],
      "SELECT name, birth_year FROM travelers WHERE home_city = '{city}'", {"city": "SELECT DISTINCT home_city FROM travelers"}),
]

TARGET = {0: 0.50, 1: 0.15, 2: 0.35}  # JOIN 0개, 1개, 2개 이상 (외부 질문 118문항 분포: 59, 18, 41)


def bucket(joins: int) -> int:
    return min(joins, 2)


def generate(templates, root, cap, eval_questions, rnd):
    """템플릿마다 실행 검증을 통과한 예시를 만든다. 반환: [(템플릿 번호, 예시)]"""
    schemas, conns = {}, {}
    rows, seen, dropped = [], set(), Counter()
    for tid, t in enumerate(templates):
        db = t["db"]
        if db not in conns:
            path = db_path_for(root, db)
            conns[db] = sqlite3.connect(path)
            schemas[db] = get_schema(path)
        conn = conns[db]
        kept = 0
        for params in combos(conn, t["params"], rnd):
            if kept >= min(t["cap"], cap):
                break
            sql = t["sql"].format(**params)
            try:
                result = conn.execute(sql).fetchall()
            except sqlite3.Error as e:
                raise SystemExit(f"템플릿 {tid} SQL 오류: {e}\n{sql}")
            if not result or all(v is None for r in result for v in r) or result == [(0,)]:
                dropped["빈 결과"] += 1
                continue
            if t["rank"] and ambiguous(conn, t["rank"].format(**params), sql):
                dropped["동점"] += 1
                continue
            phrasings = t["qs"] if not params else rnd.sample(t["qs"], min(2, len(t["qs"])))
            for q in phrasings:
                q = q.format(**params)
                if q in seen or q in eval_questions:
                    dropped["평가 질문과 겹침" if q in eval_questions else "중복"] += 1
                    continue
                seen.add(q)
                rows.append((tid, {"db_id": db, "question": q, "query": sql,
                                   "messages": build_messages(schemas[db], q, sql), "joins": join_count(sql)}))
            kept += 1
    return rows, dropped


def spread_pick(items, k, rnd):
    """템플릿마다 돌아가며 하나씩 뽑아, 한 템플릿이 몰리지 않게 k개를 고른다."""
    by_t = defaultdict(list)
    for tid, r in items:
        by_t[tid].append(r)
    for v in by_t.values():
        rnd.shuffle(v)
    order = list(by_t)
    rnd.shuffle(order)
    out = []
    while len(out) < k and any(by_t.values()):
        for tid in order:
            if by_t[tid] and len(out) < k:
                out.append((tid, by_t[tid].pop()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/korean_train/database")
    ap.add_argument("--out", default="data/korean_train/train_ko_v3.jsonl")
    ap.add_argument("--total", type=int, default=1000, help="한국어 예시 수 (v2는 940)")
    ap.add_argument("--cap", type=int, default=24, help="템플릿 하나에서 쓰는 값 조합 상한 (v2와 같음)")
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()
    rnd = random.Random(args.seed)

    eval_questions = set()
    for f in ["data/korean/questions.json", "data/korean/questions_external.json"]:
        eval_questions |= {q["question"] for q in json.loads(Path(f).read_text(encoding="utf-8"))}

    templates = TEMPLATES + NEW_TEMPLATES
    pool, dropped = generate(templates, args.root, args.cap, eval_questions, rnd)

    by_bucket = defaultdict(list)
    for tid, r in pool:
        by_bucket[bucket(r["joins"])].append((tid, r))
    want = {b: round(args.total * p) for b, p in TARGET.items()}
    short = {b: f"{len(by_bucket[b])}/{want[b]}" for b in want if len(by_bucket[b]) < want[b]}
    if short:
        raise SystemExit(f"후보가 모자람 (있음/필요): {short}. --total을 줄이거나 --cap을 늘리세요.")

    picked = []
    for b in TARGET:
        picked += spread_pick(by_bucket[b], want[b], rnd)
    rnd.shuffle(picked)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for _, r in picked:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    rows = [r for _, r in picked]
    names = {0: "0개", 1: "1개", 2: "2개 이상"}
    used = Counter(tid for tid, _ in picked)
    print(f"템플릿 {len(templates)}개 (v2 {len(TEMPLATES)} + 새로 {len(NEW_TEMPLATES)}), 실제로 쓰인 템플릿 {len(used)}개")
    print(f"후보 {len(pool)}개 중 {len(rows)}개 -> {args.out}")
    print("JOIN 수별:", {names[b]: f"{n} ({n / len(rows):.0%})" for b, n in sorted(Counter(bucket(r['joins']) for r in rows).items())})
    print("DB별:", dict(Counter(r["db_id"] for r in rows)))
    print(f"템플릿당 최대 {max(used.values())}개")
    print("버린 예시:", dict(dropped))


if __name__ == "__main__":
    main()
