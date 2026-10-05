"""학습용 DB 4개에서 한국어 질문 + 정답 SQL을 템플릿으로 만든다.

    python scripts/build_korean_train_dbs.py
    python scripts/gen_korean_train.py      # -> data/korean_train/train_ko.jsonl

- 값(지역, 장르 등)은 실제 DB에서 뽑아 넣는다.
- 모든 SQL을 실행해 오류, 빈 결과, 정렬 동점(정답이 모호함)인 예시는 버린다.
- 평가용 쇼핑몰 DB(shop)와 그 질문은 쓰지 않는다.
"""

import argparse
import itertools
import json
import random
import re
import sqlite3
from collections import Counter
from pathlib import Path

from text2sql.prompt import build_messages
from text2sql.schema import db_path_for, get_schema

MONTHS = [{"m": m, "mm": f"{m:02d}", "last": [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]} for m in range(1, 13)]


def T(db, qs, sql, params=None, rank=None, cap=24):
    """템플릿 하나. params: {이름: SQL 또는 값 목록} 또는 {"pair": (이름1, 이름2, SQL)}.
    rank: ORDER BY 기준값만 뽑는 SQL. 상위 몇 개 안에서 동점이면 버린다."""
    return {"db": db, "qs": qs, "sql": sql, "params": params or {}, "rank": rank, "cap": cap}


L, H, A, V = "library", "hospital", "academy", "travel"
J_LB = "loans AS T1 JOIN books AS T2 ON T1.book_id = T2.book_id"

TEMPLATES = [
    # ---------------- 도서관 ----------------
    T(L, ["{district}에 사는 회원은 몇 명이야?", "{district} 거주 회원 수를 알려 주세요.", "{district}에 주소를 둔 회원이 몇 명인지 궁금해."],
      "SELECT count(*) FROM members WHERE district = '{district}'", {"district": "SELECT DISTINCT district FROM members"}),
    T(L, ["{year}년에 출간된 책 제목을 알려 줘.", "{year}년에 나온 책은 뭐가 있어?"],
      "SELECT title FROM books WHERE published_year = {year}", {"year": "SELECT DISTINCT published_year FROM books"}),
    T(L, ["대출 상태별로 건수를 세어 줘.", "대출 건이 상태마다 몇 건씩인지 보여 줘."],
      "SELECT status, count(*) FROM loans GROUP BY status"),
    T(L, ["쪽수가 가장 많은 책의 제목과 쪽수는?", "제일 두꺼운 책이 뭐야? 제목이랑 쪽수 알려 줘."],
      "SELECT title, pages FROM books ORDER BY pages DESC LIMIT 1", rank="SELECT pages FROM books ORDER BY pages DESC"),
    T(L, ["장르별 책 권수를 알려 줘.", "장르마다 책이 몇 권씩 있는지 보여 줘."],
      "SELECT T2.name, count(*) FROM books AS T1 JOIN genres AS T2 ON T1.genre_id = T2.genre_id GROUP BY T2.genre_id"),
    T(L, ["{author} 작가가 쓴 책 제목을 알려 줘.", "{author} 작가의 책은 어떤 게 있어?"],
      "SELECT T1.title FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id WHERE T2.name = '{author}'",
      {"author": "SELECT DISTINCT T2.name FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id"}),
    T(L, ["{nat} 작가가 쓴 책은 모두 몇 권이야?", "국적이 {nat}인 작가들의 책 수를 구해 줘."],
      "SELECT count(*) FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.author_id WHERE T2.nationality = '{nat}'",
      {"nat": "SELECT DISTINCT nationality FROM authors"}),
    T(L, ["{genre} 장르 책의 평균 쪽수는?", "{genre} 책들은 평균 몇 쪽이야?"],
      "SELECT avg(T1.pages) FROM books AS T1 JOIN genres AS T2 ON T1.genre_id = T2.genre_id WHERE T2.name = '{genre}'",
      {"genre": "SELECT name FROM genres"}),
    T(L, ["{district} 회원들의 대출 건수는 모두 몇 건이야?", "{district}에 사는 회원들이 책을 빌린 횟수를 세어 줘."],
      "SELECT count(*) FROM members AS T1 JOIN loans AS T2 ON T1.member_id = T2.member_id WHERE T1.district = '{district}'",
      {"district": "SELECT DISTINCT district FROM members"}),
    T(L, ["{member} 회원이 빌린 책 제목을 알려 줘.", "{member} 님이 대출한 책 목록을 보여 줘."],
      "SELECT T3.title FROM members AS T1 JOIN loans AS T2 ON T1.member_id = T2.member_id JOIN books AS T3 ON T2.book_id = T3.book_id WHERE T1.name = '{member}'",
      {"member": "SELECT DISTINCT T1.name FROM members AS T1 JOIN loans AS T2 ON T1.member_id = T2.member_id"}, cap=36),
    T(L, ["{genre} 장르 책은 모두 몇 번 대출됐어?", "{genre} 책의 대출 건수를 알려 줘."],
      f"SELECT count(*) FROM {J_LB} JOIN genres AS T3 ON T2.genre_id = T3.genre_id WHERE T3.name = '{{genre}}'",
      {"genre": "SELECT name FROM genres"}),
    T(L, ["연체 중인 대출의 회원 이름과 책 제목을 보여 줘.", "연체된 대출 건마다 누가 어떤 책을 빌렸는지 알려 줘."],
      "SELECT T1.name, T3.title FROM members AS T1 JOIN loans AS T2 ON T1.member_id = T2.member_id JOIN books AS T3 ON T2.book_id = T3.book_id WHERE T2.status = '연체'"),
    T(L, ["대출 횟수가 가장 많은 작가 3명의 이름과 대출 횟수를 많은 순으로 알려 줘."],
      f"SELECT T3.name, count(*) FROM {J_LB} JOIN authors AS T3 ON T2.author_id = T3.author_id GROUP BY T3.author_id ORDER BY count(*) DESC LIMIT 3",
      rank=f"SELECT count(*) FROM {J_LB} JOIN authors AS T3 ON T2.author_id = T3.author_id GROUP BY T3.author_id ORDER BY count(*) DESC"),
    T(L, ["{district} 회원들이 빌린 책을 장르별로 대출 건수를 세어 줘.", "{district}에 사는 회원들의 장르별 대출 건수를 알려 줘."],
      "SELECT T4.name, count(*) FROM members AS T1 JOIN loans AS T2 ON T1.member_id = T2.member_id JOIN books AS T3 ON T2.book_id = T3.book_id JOIN genres AS T4 ON T3.genre_id = T4.genre_id WHERE T1.district = '{district}' GROUP BY T4.genre_id",
      {"district": "SELECT DISTINCT district FROM members"}),
    T(L, ["{nat} 작가의 책을 빌린 적이 있는 회원은 몇 명이야?", "{nat} 작가 책을 한 번이라도 대출한 회원 수를 알려 줘."],
      f"SELECT count(DISTINCT T1.member_id) FROM {J_LB} JOIN authors AS T3 ON T2.author_id = T3.author_id WHERE T3.nationality = '{{nat}}'",
      {"nat": "SELECT DISTINCT nationality FROM authors"}),
    T(L, ["{genre} 장르 책을 빌린 적 있는 회원 이름을 중복 없이 알려 줘."],
      "SELECT DISTINCT T1.name FROM members AS T1 JOIN loans AS T2 ON T1.member_id = T2.member_id JOIN books AS T3 ON T2.book_id = T3.book_id JOIN genres AS T4 ON T3.genre_id = T4.genre_id WHERE T4.name = '{genre}'",
      {"genre": "SELECT name FROM genres"}),
    T(L, ["리뷰 평균 평점이 가장 높은 장르는?", "평점 평균이 제일 좋은 장르가 뭐야?"],
      "SELECT T3.name FROM book_reviews AS T1 JOIN books AS T2 ON T1.book_id = T2.book_id JOIN genres AS T3 ON T2.genre_id = T3.genre_id GROUP BY T3.genre_id ORDER BY avg(T1.rating) DESC LIMIT 1",
      rank="SELECT avg(T1.rating) FROM book_reviews AS T1 JOIN books AS T2 ON T1.book_id = T2.book_id JOIN genres AS T3 ON T2.genre_id = T3.genre_id GROUP BY T3.genre_id ORDER BY avg(T1.rating) DESC"),
    T(L, ["{ms} 회원들이 가장 많이 빌린 작가는 누구야?", "{ms} 등급 회원의 대출이 제일 많은 작가 이름을 알려 줘."],
      "SELECT T4.name FROM members AS T1 JOIN loans AS T2 ON T1.member_id = T2.member_id JOIN books AS T3 ON T2.book_id = T3.book_id JOIN authors AS T4 ON T3.author_id = T4.author_id WHERE T1.membership = '{ms}' GROUP BY T4.author_id ORDER BY count(*) DESC LIMIT 1",
      {"ms": "SELECT DISTINCT membership FROM members"},
      rank="SELECT count(*) FROM members AS T1 JOIN loans AS T2 ON T1.member_id = T2.member_id JOIN books AS T3 ON T2.book_id = T3.book_id JOIN authors AS T4 ON T3.author_id = T4.author_id WHERE T1.membership = '{ms}' GROUP BY T4.author_id ORDER BY count(*) DESC"),
    T(L, ["한 번도 대출되지 않은 책 제목을 알려 줘.", "아무도 빌려 가지 않은 책은 뭐야?"],
      "SELECT title FROM books WHERE book_id NOT IN (SELECT book_id FROM loans)"),
    T(L, ["{g1} 책과 {g2} 책을 모두 빌려 본 회원은 몇 명이야?"],
      f"SELECT count(*) FROM (SELECT T1.member_id FROM {J_LB} JOIN genres AS T3 ON T2.genre_id = T3.genre_id WHERE T3.name = '{{g1}}' INTERSECT SELECT T1.member_id FROM {J_LB} JOIN genres AS T3 ON T2.genre_id = T3.genre_id WHERE T3.name = '{{g2}}')",
      {"pair": ("g1", "g2", "SELECT name FROM genres")}),

    # ---------------- 병원 ----------------
    T(H, ["{region}에 사는 환자는 몇 명이야?", "{region} 거주 환자 수를 알려 주세요."],
      "SELECT count(*) FROM patients WHERE region = '{region}'", {"region": "SELECT DISTINCT region FROM patients"}),
    T(H, ["보험 유형별 환자 수를 알려 줘.", "환자들을 보험 종류마다 몇 명씩인지 세어 줘."],
      "SELECT insurance, count(*) FROM patients GROUP BY insurance"),
    T(H, ["2025년 {m}월에 잡힌 진료는 몇 건이야?", "2025년 {m}월 진료 건수를 알려 줘."],
      "SELECT count(*) FROM appointments WHERE visit_date BETWEEN '2025-{mm}-01' AND '2025-{mm}-{last}'", {"_": MONTHS}),
    T(H, ["진료과별 의사 수를 알려 줘.", "과마다 의사가 몇 명씩 있어?"],
      "SELECT T2.name, count(*) FROM doctors AS T1 JOIN departments AS T2 ON T1.dept_id = T2.dept_id GROUP BY T2.dept_id"),
    T(H, ["{dept} 의사들의 이름과 경력 연수를 보여 줘.", "{dept}에 있는 의사 이름이랑 경력이 궁금해."],
      "SELECT T1.name, T1.career_years FROM doctors AS T1 JOIN departments AS T2 ON T1.dept_id = T2.dept_id WHERE T2.name = '{dept}'",
      {"dept": "SELECT name FROM departments"}),
    T(H, ["{dept} 진료는 모두 몇 건이야?", "{dept}에서 본 진료 건수를 세어 줘."],
      "SELECT count(*) FROM appointments AS T1 JOIN doctors AS T2 ON T1.doctor_id = T2.doctor_id JOIN departments AS T3 ON T2.dept_id = T3.dept_id WHERE T3.name = '{dept}'",
      {"dept": "SELECT name FROM departments"}),
    T(H, ["{doctor} 의사가 진료를 마친 환자는 중복 없이 몇 명이야?"],
      "SELECT count(DISTINCT T1.patient_id) FROM appointments AS T1 JOIN doctors AS T2 ON T1.doctor_id = T2.doctor_id WHERE T2.name = '{doctor}' AND T1.status = '진료완료'",
      {"doctor": "SELECT name FROM doctors"}),
    T(H, ["{patient} 환자가 진료받은 진료과 이름을 중복 없이 알려 줘.", "{patient} 환자는 어느 과에서 진료를 받았어?"],
      "SELECT DISTINCT T4.name FROM patients AS T1 JOIN appointments AS T2 ON T1.patient_id = T2.patient_id JOIN doctors AS T3 ON T2.doctor_id = T3.doctor_id JOIN departments AS T4 ON T3.dept_id = T4.dept_id WHERE T1.name = '{patient}'",
      {"patient": "SELECT DISTINCT T1.name FROM patients AS T1 JOIN appointments AS T2 ON T1.patient_id = T2.patient_id"}, cap=36),
    T(H, ["{drug}을 처방받은 환자는 중복 없이 몇 명이야?", "{drug} 처방을 받은 적 있는 환자 수를 알려 줘."],
      "SELECT count(DISTINCT T2.patient_id) FROM prescriptions AS T1 JOIN appointments AS T2 ON T1.appt_id = T2.appt_id JOIN drugs AS T3 ON T1.drug_id = T3.drug_id WHERE T3.name = '{drug}'",
      {"drug": "SELECT name FROM drugs"}),
    T(H, ["{dept}에서 처방된 약 이름을 중복 없이 알려 줘.", "{dept} 진료에서 나간 약 목록을 보여 줘."],
      "SELECT DISTINCT T5.name FROM departments AS T1 JOIN doctors AS T2 ON T1.dept_id = T2.dept_id JOIN appointments AS T3 ON T2.doctor_id = T3.doctor_id JOIN prescriptions AS T4 ON T3.appt_id = T4.appt_id JOIN drugs AS T5 ON T4.drug_id = T5.drug_id WHERE T1.name = '{dept}'",
      {"dept": "SELECT name FROM departments"}),
    T(H, ["처방 건수가 가장 많은 진료과는 어디야?", "약을 제일 많이 처방한 과는?"],
      "SELECT T4.name FROM prescriptions AS T1 JOIN appointments AS T2 ON T1.appt_id = T2.appt_id JOIN doctors AS T3 ON T2.doctor_id = T3.doctor_id JOIN departments AS T4 ON T3.dept_id = T4.dept_id GROUP BY T4.dept_id ORDER BY count(*) DESC LIMIT 1",
      rank="SELECT count(*) FROM prescriptions AS T1 JOIN appointments AS T2 ON T1.appt_id = T2.appt_id JOIN doctors AS T3 ON T2.doctor_id = T3.doctor_id JOIN departments AS T4 ON T3.dept_id = T4.dept_id GROUP BY T4.dept_id ORDER BY count(*) DESC"),
    T(H, ["취소된 진료를 빼고 {region} 환자들의 진료비 합계를 구해 줘."],
      "SELECT sum(T2.fee) FROM patients AS T1 JOIN appointments AS T2 ON T1.patient_id = T2.patient_id WHERE T1.region = '{region}' AND T2.status != '취소'",
      {"region": "SELECT DISTINCT region FROM patients"}),
    T(H, ["{ins} 환자에게 가장 많이 처방된 약은 뭐야?"],
      "SELECT T4.name FROM patients AS T1 JOIN appointments AS T2 ON T1.patient_id = T2.patient_id JOIN prescriptions AS T3 ON T2.appt_id = T3.appt_id JOIN drugs AS T4 ON T3.drug_id = T4.drug_id WHERE T1.insurance = '{ins}' GROUP BY T4.drug_id ORDER BY count(*) DESC LIMIT 1",
      {"ins": "SELECT DISTINCT insurance FROM patients"},
      rank="SELECT count(*) FROM patients AS T1 JOIN appointments AS T2 ON T1.patient_id = T2.patient_id JOIN prescriptions AS T3 ON T2.appt_id = T3.appt_id JOIN drugs AS T4 ON T3.drug_id = T4.drug_id WHERE T1.insurance = '{ins}' GROUP BY T4.drug_id ORDER BY count(*) DESC"),
    T(H, ["평균 진료비보다 비싼 진료를 받은 환자 이름을 중복 없이 알려 줘."],
      "SELECT DISTINCT T1.name FROM patients AS T1 JOIN appointments AS T2 ON T1.patient_id = T2.patient_id WHERE T2.fee > (SELECT avg(fee) FROM appointments)"),
    T(H, ["{d1}와 {d2} 진료를 둘 다 받은 환자는 몇 명이야?"],
      "SELECT count(*) FROM (SELECT T1.patient_id FROM appointments AS T1 JOIN doctors AS T2 ON T1.doctor_id = T2.doctor_id JOIN departments AS T3 ON T2.dept_id = T3.dept_id WHERE T3.name = '{d1}' INTERSECT SELECT T1.patient_id FROM appointments AS T1 JOIN doctors AS T2 ON T1.doctor_id = T2.doctor_id JOIN departments AS T3 ON T2.dept_id = T3.dept_id WHERE T3.name = '{d2}')",
      {"pair": ("d1", "d2", "SELECT name FROM departments")}),
    T(H, ["{dept}에서 처방한 약값 총액(1정 가격 × 처방 일수 × 하루 횟수의 합)은 얼마야?"],
      "SELECT sum(T5.unit_price * T4.days * T4.daily_dose) FROM departments AS T1 JOIN doctors AS T2 ON T1.dept_id = T2.dept_id JOIN appointments AS T3 ON T2.doctor_id = T3.doctor_id JOIN prescriptions AS T4 ON T3.appt_id = T4.appt_id JOIN drugs AS T5 ON T4.drug_id = T5.drug_id WHERE T1.name = '{dept}'",
      {"dept": "SELECT name FROM departments"}),
    T(H, ["제약사별 처방 건수를 구해 줘.", "제약회사마다 처방이 몇 건씩 나갔어?"],
      "SELECT T2.maker, count(*) FROM prescriptions AS T1 JOIN drugs AS T2 ON T1.drug_id = T2.drug_id GROUP BY T2.maker"),

    # ---------------- 학원 ----------------
    T(A, ["{grade} 학생은 몇 명이야?", "학년이 {grade}인 학생 수를 알려 줘."],
      "SELECT count(*) FROM students WHERE school_grade = '{grade}'", {"grade": "SELECT DISTINCT school_grade FROM students"}),
    T(A, ["{school} 학생들 이름을 알려 줘.", "{school}에 다니는 학생은 누구누구야?"],
      "SELECT name FROM students WHERE school_name = '{school}'", {"school": "SELECT DISTINCT school_name FROM students"}),
    T(A, ["수강 상태별 등록 건수를 알려 줘.", "등록을 상태마다 몇 건씩인지 세어 줘."],
      "SELECT status, count(*) FROM enrollments GROUP BY status"),
    T(A, ["{level} 강좌의 평균 월 수강료는 얼마야?"],
      "SELECT avg(monthly_fee) FROM courses WHERE level = '{level}'", {"level": "SELECT DISTINCT level FROM courses"}),
    T(A, ["과목별 강좌 수를 알려 줘.", "과목마다 강좌가 몇 개씩 열려 있어?"],
      "SELECT T2.name, count(*) FROM courses AS T1 JOIN subjects AS T2 ON T1.subject_id = T2.subject_id GROUP BY T2.subject_id"),
    T(A, ["{teacher} 선생님이 맡은 강좌 제목과 요일은?", "{teacher} 선생님 수업은 무슨 강좌고 무슨 요일이야?"],
      "SELECT T1.title, T1.weekday FROM courses AS T1 JOIN teachers AS T2 ON T1.teacher_id = T2.teacher_id WHERE T2.name = '{teacher}'",
      {"teacher": "SELECT name FROM teachers"}),
    T(A, ["{subject} 과목 선생님 이름을 알려 줘."],
      "SELECT T1.name FROM teachers AS T1 JOIN subjects AS T2 ON T1.subject_id = T2.subject_id WHERE T2.name = '{subject}'",
      {"subject": "SELECT name FROM subjects"}),
    T(A, ["{student} 학생이 등록한 강좌 제목을 알려 줘.", "{student} 학생은 어떤 강좌를 들어?"],
      "SELECT T3.title FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id JOIN courses AS T3 ON T2.course_id = T3.course_id WHERE T1.name = '{student}'",
      {"student": "SELECT DISTINCT T1.name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id"}, cap=36),
    T(A, ["{subject} 강좌에 등록한 학생은 중복 없이 몇 명이야?"],
      "SELECT count(DISTINCT T1.student_id) FROM enrollments AS T1 JOIN courses AS T2 ON T1.course_id = T2.course_id JOIN subjects AS T3 ON T2.subject_id = T3.subject_id WHERE T3.name = '{subject}'",
      {"subject": "SELECT name FROM subjects"}),
    T(A, ["{subject} 시험의 평균 점수는?", "{subject} 강좌 시험 점수 평균을 구해 줘."],
      "SELECT avg(T1.score) FROM exams AS T1 JOIN enrollments AS T2 ON T1.enroll_id = T2.enroll_id JOIN courses AS T3 ON T2.course_id = T3.course_id JOIN subjects AS T4 ON T3.subject_id = T4.subject_id WHERE T4.name = '{subject}'",
      {"subject": "SELECT name FROM subjects"}),
    T(A, ["{school} 학생들이 가장 많이 등록한 과목은?"],
      "SELECT T4.name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id JOIN courses AS T3 ON T2.course_id = T3.course_id JOIN subjects AS T4 ON T3.subject_id = T4.subject_id WHERE T1.school_name = '{school}' GROUP BY T4.subject_id ORDER BY count(*) DESC LIMIT 1",
      {"school": "SELECT DISTINCT school_name FROM students"},
      rank="SELECT count(*) FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id JOIN courses AS T3 ON T2.course_id = T3.course_id JOIN subjects AS T4 ON T3.subject_id = T4.subject_id WHERE T1.school_name = '{school}' GROUP BY T4.subject_id ORDER BY count(*) DESC"),
    T(A, ["시험 평균 점수가 가장 높은 선생님은 누구야?", "담당 강좌 학생들의 시험 평균이 제일 높은 선생님 이름을 알려 줘."],
      "SELECT T4.name FROM exams AS T1 JOIN enrollments AS T2 ON T1.enroll_id = T2.enroll_id JOIN courses AS T3 ON T2.course_id = T3.course_id JOIN teachers AS T4 ON T3.teacher_id = T4.teacher_id GROUP BY T4.teacher_id ORDER BY avg(T1.score) DESC LIMIT 1",
      rank="SELECT avg(T1.score) FROM exams AS T1 JOIN enrollments AS T2 ON T1.enroll_id = T2.enroll_id JOIN courses AS T3 ON T2.course_id = T3.course_id JOIN teachers AS T4 ON T3.teacher_id = T4.teacher_id GROUP BY T4.teacher_id ORDER BY avg(T1.score) DESC"),
    T(A, ["{wd}요일 강좌를 듣는 학생 이름을 중복 없이 알려 줘."],
      "SELECT DISTINCT T1.name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id JOIN courses AS T3 ON T2.course_id = T3.course_id WHERE T3.weekday = '{wd}'",
      {"wd": "SELECT DISTINCT weekday FROM courses"}),
    T(A, ["등록한 학생이 한 명도 없는 강좌 제목은?"],
      "SELECT title FROM courses WHERE course_id NOT IN (SELECT course_id FROM enrollments)"),
    T(A, ["수강중인 등록만 보고 {grade} 학생들이 내는 월 수강료 합계를 구해 줘."],
      "SELECT sum(T3.monthly_fee) FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id JOIN courses AS T3 ON T2.course_id = T3.course_id WHERE T1.school_grade = '{grade}' AND T2.status = '수강중'",
      {"grade": "SELECT DISTINCT school_grade FROM students"}),
    T(A, ["{s1}와 {s2}를 둘 다 듣는 학생은 몇 명이야?"],
      "SELECT count(*) FROM (SELECT T1.student_id FROM enrollments AS T1 JOIN courses AS T2 ON T1.course_id = T2.course_id JOIN subjects AS T3 ON T2.subject_id = T3.subject_id WHERE T3.name = '{s1}' INTERSECT SELECT T1.student_id FROM enrollments AS T1 JOIN courses AS T2 ON T1.course_id = T2.course_id JOIN subjects AS T3 ON T2.subject_id = T3.subject_id WHERE T3.name = '{s2}')",
      {"pair": ("s1", "s2", "SELECT name FROM subjects")}),
    T(A, ["{level} 강좌 시험에서 90점 이상을 받은 학생 이름을 중복 없이 알려 줘."],
      "SELECT DISTINCT T1.name FROM students AS T1 JOIN enrollments AS T2 ON T1.student_id = T2.student_id JOIN courses AS T3 ON T2.course_id = T3.course_id JOIN exams AS T4 ON T2.enroll_id = T4.enroll_id WHERE T3.level = '{level}' AND T4.score >= 90",
      {"level": "SELECT DISTINCT level FROM courses"}),

    # ---------------- 여행사 ----------------
    T(V, ["{city}에 사는 여행객은 몇 명이야?", "{city} 거주 고객 수를 알려 줘."],
      "SELECT count(*) FROM travelers WHERE home_city = '{city}'", {"city": "SELECT DISTINCT home_city FROM travelers"}),
    T(V, ["{season} 시즌 패키지 제목과 가격을 보여 줘.", "{season}에 출발하는 패키지는 뭐가 있고 얼마야?"],
      "SELECT title, price FROM packages WHERE season = '{season}'", {"season": "SELECT DISTINCT season FROM packages"}),
    T(V, ["예약 상태별 건수를 알려 줘."], "SELECT status, count(*) FROM bookings GROUP BY status"),
    T(V, ["가장 비싼 패키지의 제목과 가격은?", "제일 비싼 여행 상품이 뭐야? 가격도 알려 줘."],
      "SELECT title, price FROM packages ORDER BY price DESC LIMIT 1", rank="SELECT price FROM packages ORDER BY price DESC"),
    T(V, ["지역별 호텔 수를 알려 줘.", "지역마다 호텔이 몇 개씩 있어?"],
      "SELECT T2.name, count(*) FROM hotels AS T1 JOIN regions AS T2 ON T1.region_id = T2.region_id GROUP BY T2.region_id"),
    T(V, ["{stars}성급 호텔이 있는 지역 이름을 중복 없이 알려 줘."],
      "SELECT DISTINCT T2.name FROM hotels AS T1 JOIN regions AS T2 ON T1.region_id = T2.region_id WHERE T1.stars = {stars}",
      {"stars": "SELECT DISTINCT stars FROM hotels"}),
    T(V, ["{region} 호텔 패키지의 평균 가격은?", "{region} 여행 패키지는 평균 얼마야?"],
      "SELECT avg(T1.price) FROM packages AS T1 JOIN hotels AS T2 ON T1.hotel_id = T2.hotel_id JOIN regions AS T3 ON T2.region_id = T3.region_id WHERE T3.name = '{region}'",
      {"region": "SELECT name FROM regions"}),
    T(V, ["{traveler} 고객이 예약한 패키지 제목을 알려 줘.", "{traveler} 님은 어떤 패키지를 예약했어?"],
      "SELECT T3.title FROM travelers AS T1 JOIN bookings AS T2 ON T1.traveler_id = T2.traveler_id JOIN packages AS T3 ON T2.package_id = T3.package_id WHERE T1.name = '{traveler}'",
      {"traveler": "SELECT DISTINCT T1.name FROM travelers AS T1 JOIN bookings AS T2 ON T1.traveler_id = T2.traveler_id"}, cap=36),
    T(V, ["취소를 빼고 {country} 여행 예약은 몇 건이야?", "{country} 패키지 예약 건수를 알려 줘. 취소된 건 제외하고."],
      "SELECT count(*) FROM bookings AS T1 JOIN packages AS T2 ON T1.package_id = T2.package_id JOIN hotels AS T3 ON T2.hotel_id = T3.hotel_id JOIN regions AS T4 ON T3.region_id = T4.region_id WHERE T4.country = '{country}' AND T1.status != '취소'",
      {"country": "SELECT DISTINCT country FROM regions"}),
    T(V, ["{city} 출신 여행객들이 예약한 지역 이름을 중복 없이 알려 줘."],
      "SELECT DISTINCT T5.name FROM travelers AS T1 JOIN bookings AS T2 ON T1.traveler_id = T2.traveler_id JOIN packages AS T3 ON T2.package_id = T3.package_id JOIN hotels AS T4 ON T3.hotel_id = T4.hotel_id JOIN regions AS T5 ON T4.region_id = T5.region_id WHERE T1.home_city = '{city}'",
      {"city": "SELECT DISTINCT home_city FROM travelers"}),
    T(V, ["취소를 제외하고 예약 인원 합계가 가장 많은 지역은 어디야?"],
      "SELECT T4.name FROM bookings AS T1 JOIN packages AS T2 ON T1.package_id = T2.package_id JOIN hotels AS T3 ON T2.hotel_id = T3.hotel_id JOIN regions AS T4 ON T3.region_id = T4.region_id WHERE T1.status != '취소' GROUP BY T4.region_id ORDER BY sum(T1.people) DESC LIMIT 1",
      rank="SELECT sum(T1.people) FROM bookings AS T1 JOIN packages AS T2 ON T1.package_id = T2.package_id JOIN hotels AS T3 ON T2.hotel_id = T3.hotel_id JOIN regions AS T4 ON T3.region_id = T4.region_id WHERE T1.status != '취소' GROUP BY T4.region_id ORDER BY sum(T1.people) DESC"),
    T(V, ["여행 후기 평균 평점이 가장 높은 지역은?", "후기 별점 평균이 제일 좋은 여행지는 어디야?"],
      "SELECT T5.name FROM trip_reviews AS T1 JOIN bookings AS T2 ON T1.booking_id = T2.booking_id JOIN packages AS T3 ON T2.package_id = T3.package_id JOIN hotels AS T4 ON T3.hotel_id = T4.hotel_id JOIN regions AS T5 ON T4.region_id = T5.region_id GROUP BY T5.region_id ORDER BY avg(T1.rating) DESC LIMIT 1",
      rank="SELECT avg(T1.rating) FROM trip_reviews AS T1 JOIN bookings AS T2 ON T1.booking_id = T2.booking_id JOIN packages AS T3 ON T2.package_id = T3.package_id JOIN hotels AS T4 ON T3.hotel_id = T4.hotel_id JOIN regions AS T5 ON T4.region_id = T5.region_id GROUP BY T5.region_id ORDER BY avg(T1.rating) DESC"),
    T(V, ["취소를 제외한 지역별 매출(인원 × 1인 가격의 합)을 구해 줘."],
      "SELECT T4.name, sum(T1.people * T2.price) FROM bookings AS T1 JOIN packages AS T2 ON T1.package_id = T2.package_id JOIN hotels AS T3 ON T2.hotel_id = T3.hotel_id JOIN regions AS T4 ON T3.region_id = T4.region_id WHERE T1.status != '취소' GROUP BY T4.region_id"),
    T(V, ["{season} 패키지를 예약한 여행객은 중복 없이 몇 명이야?"],
      "SELECT count(DISTINCT T1.traveler_id) FROM bookings AS T1 JOIN packages AS T2 ON T1.package_id = T2.package_id WHERE T2.season = '{season}'",
      {"season": "SELECT DISTINCT season FROM packages"}),
    T(V, ["평균 가격보다 비싼 패키지 제목을 알려 줘."],
      "SELECT title FROM packages WHERE price > (SELECT avg(price) FROM packages)"),
    T(V, ["한 번도 예약되지 않은 패키지 제목은?", "아무도 예약하지 않은 상품이 있어? 제목을 알려 줘."],
      "SELECT title FROM packages WHERE package_id NOT IN (SELECT package_id FROM bookings)"),
    T(V, ["{r1}와 {r2}를 둘 다 여행한 고객은 몇 명이야? (여행완료 기준)"],
      "SELECT count(*) FROM (SELECT T1.traveler_id FROM bookings AS T1 JOIN packages AS T2 ON T1.package_id = T2.package_id JOIN hotels AS T3 ON T2.hotel_id = T3.hotel_id JOIN regions AS T4 ON T3.region_id = T4.region_id WHERE T4.name = '{r1}' AND T1.status = '여행완료' INTERSECT SELECT T1.traveler_id FROM bookings AS T1 JOIN packages AS T2 ON T1.package_id = T2.package_id JOIN hotels AS T3 ON T2.hotel_id = T3.hotel_id JOIN regions AS T4 ON T3.region_id = T4.region_id WHERE T4.name = '{r2}' AND T1.status = '여행완료')",
      {"pair": ("r1", "r2", "SELECT name FROM regions")}),
]


def combos(conn, params, rnd):
    if not params:
        return [{}]
    if "_" in params:
        return list(params["_"])
    if "pair" in params:
        a, b, sql = params["pair"]
        vals = [r[0] for r in conn.execute(sql)]
        return [{a: x, b: y} for x, y in itertools.permutations(vals, 2)]
    lists = {k: [r[0] for r in conn.execute(v)] for k, v in params.items()}
    out = [dict(zip(lists, vals)) for vals in itertools.product(*lists.values())]
    rnd.shuffle(out)
    return out


def ambiguous(conn, rank_sql, sql):
    """ORDER BY ... LIMIT n 에서 상위 n+1개 안에 동점이 있으면 정답이 모호하다."""
    m = re.search(r"LIMIT (\d+)$", sql)
    n = int(m.group(1)) if m else 1
    keys = [r[0] for r in conn.execute(rank_sql).fetchall()[: n + 1]]
    return len(keys) != len(set(keys))


def join_count(sql: str) -> int:
    return len(re.findall(r"\bJOIN\b", sql))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/korean_train/database")
    ap.add_argument("--out", default="data/korean_train/train_ko.jsonl")
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()
    rnd = random.Random(args.seed)
    eval_questions = {q["question"] for q in json.loads(Path("data/korean/questions.json").read_text(encoding="utf-8"))}

    schemas, conns = {}, {}
    rows, seen, dropped = [], set(), Counter()
    for t in TEMPLATES:
        db = t["db"]
        if db not in conns:
            path = db_path_for(args.root, db)
            conns[db] = sqlite3.connect(path)
            schemas[db] = get_schema(path)
        conn = conns[db]
        kept = 0
        for params in combos(conn, t["params"], rnd):
            if kept >= t["cap"]:
                break
            sql = t["sql"].format(**params)
            try:
                result = conn.execute(sql).fetchall()
            except sqlite3.Error:
                dropped["SQL 오류"] += 1
                continue
            if not result or all(v is None for r in result for v in r) or result == [(0,)]:
                dropped["빈 결과"] += 1
                continue
            if t["rank"] and ambiguous(conn, t["rank"].format(**params), sql):
                dropped["동점"] += 1
                continue
            # 파라미터 없는 템플릿은 모든 표현을, 있는 템플릿은 표현을 최대 2개까지 무작위로 쓴다
            phrasings = t["qs"] if not params else rnd.sample(t["qs"], min(2, len(t["qs"])))
            for q in phrasings:
                q = q.format(**params)
                if q in seen or q in eval_questions:
                    continue
                seen.add(q)
                rows.append({"db_id": db, "question": q, "query": sql,
                             "messages": build_messages(schemas[db], q, sql), "joins": join_count(sql)})
            kept += 1

    rnd.shuffle(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    by_db = Counter(r["db_id"] for r in rows)
    by_join = Counter(min(r["joins"], 3) for r in rows)
    print(f"{len(rows)}개 -> {args.out}")
    print("DB별:", dict(by_db))
    print("JOIN 수별:", {("3개 이상" if k == 3 else f"{k}개"): v for k, v in sorted(by_join.items())})
    print("버린 예시:", dict(dropped))


if __name__ == "__main__":
    main()
