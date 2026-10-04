# Local Text-to-SQL

자연어 질문을 SQL로 바꿔 실행해 주는 **로컬 LLM**입니다.
오픈소스 코드 모델(Qwen2.5-Coder)을 Spider 데이터셋으로 QLoRA 파인튜닝하고, Ollama로 로컬에서 서빙합니다.

```
질문 ─▶ FastAPI ─▶ 스키마 + 질문 프롬프트 ─▶ Ollama(파인튜닝 모델) ─▶ SQL
                                                                  │
          결과 ◀── 읽기 전용 · 권한 제한 · 타임아웃이 걸린 SQLite 실행 ◀┘
```

## 결과

Spider dev 세트 전체(1,034문제, DB 20개)의 실행 정확도(Execution Accuracy)입니다. 실험을 진행하면서 채웁니다.

| 모델 | 방식 | EX | SQL 오류율 | 평균 지연(CPU) |
|---|---|---|---|---|
| Qwen2.5-Coder-3B | zero-shot | 61.8% | 13.4% | 5.52s |
| Qwen2.5-Coder-3B | + 예시 행 3개 | - | - | - |
| Qwen2.5-Coder-3B | QLoRA 파인튜닝 | 73.4% | 6.1% | 5.04s |
| Qwen2.5-Coder-3B | zero-shot + self-correction | 62.6% | 10.3% | 7.57s |
| Qwen2.5-Coder-3B | QLoRA 파인튜닝 + self-correction | **74.4%** | **3.6%** | 5.97s |

### 파인튜닝 전후 비교

같은 1,034문제에서 **EX +11.6%p (61.8% → 73.4%)**, SQL 오류율은 절반 이하(13.4% → 6.1%)로 줄었습니다.
문제별로 보면 176문제가 새로 맞고 56문제가 새로 틀려 순증 120문제입니다. 부호 검정 기준 z ≈ 7.9로, 우연으로 보기 어려운 차이입니다.

| SQL 유형 | 파인튜닝 전 | 파인튜닝 후 | 변화 |
|---|---|---|---|
| 단순 조회 | 78.1% | 88.3% | +10.2%p |
| ORDER BY | 62.4% | 74.7% | +12.2%p |
| GROUP BY | 51.6% | 66.4% | +14.8%p |
| JOIN | 51.2% | 59.6% | +8.3%p |
| 집합 연산 | 43.8% | 58.8% | +15.0%p |
| 중첩 쿼리 | 37.3% | 50.6% | +13.3%p |

| 오답 구분 | 파인튜닝 전 | 파인튜닝 후 |
|---|---|---|
| 실행 오류: 존재하지 않는 컬럼 | 129 | 61 |
| 실행 오류: 존재하지 않는 테이블 / 모호한 컬럼 / 기타 | 10 | 2 |
| 실행은 되지만 결과가 틀림 | 256 | 212 |

- **가장 큰 변화는 "불필요한 JOIN"이 사라진 것**입니다. 베이스라인은 `singer` 테이블 하나로 답할 수 있는 질문에도 테이블 3~5개를 JOIN하다가, 없는 `song` 테이블이나 엉뚱한 별칭(`T2.Country`)을 만들어 냈습니다. 파인튜닝 모델은 필요한 테이블만 씁니다.
  - 질문: *What is the name and capacity for the stadium with highest average attendance?*
  - 전: `SELECT T2.Name, T2.Capacity FROM stadium AS T1 JOIN concert AS T2 ... ORDER BY T1.Average DESC LIMIT 1` → `no such column: T2.Name`
  - 후: `SELECT name, capacity FROM stadium ORDER BY average DESC LIMIT 1` ✓
- 설명문이나 코드펜스 없이 **SQL 한 줄만** 출력하게 되어 응답이 짧아졌고, 평균 지연도 9% 줄었습니다.
- 어려운 DB에서 개선 폭이 컸습니다: `course_teach` 37% → 70%, `world_1` 37% → 52%, `car_1` 34% → 49%.
- **나빠진 사례(56문제)**:
  - 학습 데이터 스타일의 컬럼명을 지어내는 경우가 있습니다. 예: 실제 `PetType` 대신 `pet_type`, `ContId` 대신 `ContinentId`. 남은 "존재하지 않는 컬럼" 오류 61건 중 33건이 `car_1`과 `world_1`에 몰려 있습니다. → self-correction 루프로 줄일 계획입니다.
  - "oldest to youngest"를 `ASC`로 쓰는 등 정렬 방향을 반대로 쓰거나, `count(*), country`처럼 컬럼 순서를 바꾼 경우도 있습니다.
- 참고로, 이 평가는 컬럼 순서까지 비교하는 엄격한 방식입니다. 행 값은 같고 컬럼 순서만 다른 오답이 베이스라인 39건, 파인튜닝 32건으로 비슷해서, 이 방식이 비교 결과를 한쪽으로 치우치게 하지는 않습니다.

상세 비교는 `python scripts/compare.py outputs/preds_base-3b_eval.jsonl outputs/preds_ft-3b_eval.jsonl`로 재현할 수 있습니다.

### Self-correction 실험

실행 오류가 난 SQL만 SQLite 오류 메시지와 함께 모델에 다시 보여 주고 고치게 했습니다 (최대 2회). 정답 SQL은 쓰지 않으므로 실제 서비스에서도 같은 효과를 기대할 수 있습니다.

| | 재시도한 문제 | 실행 성공으로 바뀜 | 그중 정답 | EX 변화 | 평균 지연 변화 |
|---|---|---|---|---|---|
| zero-shot | 139 | 33 | 8 | +0.8%p | +2.05s |
| 파인튜닝 | 63 | 26 | 10 | +1.0%p | +0.93s |

- 실행 오류는 크게 줄었지만(파인튜닝 6.1% → 3.6%) **정답률 상승은 1%p 안팎**에 그쳤습니다. 오류만 없앤 SQL의 60% 이상은 여전히 답이 틀렸습니다.
- **잘 고친 경우는 이름을 살짝 틀린 경우**입니다. 예: `pet_type` → `pettype`, 별칭 `T2.PetType` → `T1.PetType`, 모호한 `PetID` → `T2.PetID`.
- **가장 큰 한계는 "같은 SQL 반복"**입니다. temperature 0에서 오류 메시지를 줘도 직전 SQL을 그대로 다시 쓴 경우가 zero-shot 65%(91/139), 파인튜닝 40%(25/63)였습니다. 없는 `song` 테이블처럼 잘못된 생각에서 출발한 SQL은 거의 고치지 못했습니다.
- 2번째 시도는 거의 도움이 되지 않았습니다. 성공의 대부분(파인튜닝 26건 중 24건)이 1번째 시도에서 나왔습니다.
- 개선 아이디어: 오류가 난 테이블의 실제 컬럼 목록을 힌트로 함께 주기, 재시도에서는 temperature를 올려 다른 답을 유도하기, 오류 수정 대화를 학습 데이터에 포함하기.

### 베이스라인 오류 분석 (zero-shot)

정답 SQL의 구성 요소별 정답률입니다. 한 문제가 여러 유형에 속할 수 있습니다.

| 유형 | 정답률 |
|---|---|
| 단순 조회 | 78.1% (260/333) |
| ORDER BY | 62.4% (148/237) |
| GROUP BY | 51.6% (143/277) |
| JOIN | 51.2% (209/408) |
| 집합 연산 (INTERSECT/EXCEPT/UNION) | 43.8% (35/80) |
| 중첩 쿼리 | 37.3% (31/83) |

- 오답 395건 = 실행 오류 139건(존재하지 않는 컬럼 129, 테이블 5, 모호한 컬럼 5) + 실행은 되지만 결과가 틀림 256건
- 주원인은 **스키마 연결 실패**입니다. 테이블 별칭을 혼동하거나, 엉뚱한 테이블을 JOIN하거나, GROUP BY 조건을 빠뜨렸습니다.
- DB별 편차가 큽니다: `car_1` 34%, `world_1` 37% ↔ `poker_player` 98%, `orchestra` 95%
- Spider 정답 자체의 오류도 발견했습니다. 예: "dog는 있고 cat은 없는 학생의 first name" 질문에 정답 SQL이 `fname, age`를 출력합니다.

### 학습 과정 (QLoRA)

![QLoRA fine-tuning loss](docs/loss_curve.png)

| 항목 | 값 |
|---|---|
| 학습 데이터 | Spider train 8,659문제, 1 epoch (약 1,080 step) |
| 설정 | 4bit QLoRA, r=16, alpha=16, lr 2e-4 (cosine), 배치 2 × 누적 4, Colab T4 |
| Loss | 0.404 (step 10) → **0.080** (마지막 100 step 평균), 최저 0.063 |

- 처음 200 step 안에 Loss가 절반 이하로 떨어진 뒤 끝까지 완만하게 내려갔습니다. 출렁임은 있지만 `nan`이나 급등 없이 안정적으로 수렴했습니다.
- `train_on_responses_only`로 SQL 부분에만 Loss를 계산하므로, 위 값은 "정답 SQL을 얼마나 그대로 써내는가"를 뜻합니다.
- 학습 Loss는 학습 데이터 기준이라 일반화 성능을 보장하지 않습니다. 실제 성능은 학습에 쓰지 않은 dev 세트의 실행 정확도로 판단합니다.

## 구조

```
src/text2sql/
  prompt.py      학습·추론 공통 프롬프트 + 모델 출력에서 SQL 추출
  schema.py      SQLite → CREATE TABLE 스키마 텍스트
  executor.py    안전한 SQL 실행 (읽기 전용 + authorizer + 타임아웃)
  evaluate.py    실행 정확도 계산
  llm.py         Ollama 클라이언트
  correct.py     self-correction (실행 오류 메시지로 SQL 재작성)
scripts/
  prepare_spider.py   Spider → chat 형식 JSONL
  predict.py          모델로 dev 세트 SQL 생성 (중단 후 이어서 실행 가능)
  evaluate.py         정확도·오류율·지연시간 집계
  compare.py          두 모델 결과 비교 (유형별·DB별·좋아진/나빠진 사례)
  self_correct.py     실행 오류가 난 SQL만 오류 메시지와 함께 다시 고치기
  plot_loss.py        Colab 학습 로그 → Loss 그래프 (pip install -e ".[plot]")
train/finetune_unsloth.py   Colab T4용 QLoRA 학습 → GGUF 변환
app/main.py                 FastAPI 서버 (/query, /schema, /databases)
tests/                      실행기 보안·평가 로직 테스트
```

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

### 1. 데이터 준비
[Spider 공식 사이트](https://yale-lily.github.io/spider)에서 `spider_data.zip`을 받아 `data/spider/`에 풉니다.
`data/spider/database/`, `train_spider.json`, `dev.json`이 있어야 합니다.

```bash
python scripts/prepare_spider.py
```

### 2. 베이스라인 측정
```bash
ollama pull qwen2.5-coder:3b
python scripts/predict.py --model qwen2.5-coder:3b --tag base-3b --limit 200
python scripts/evaluate.py outputs/preds_base-3b.jsonl
```

### 3. 파인튜닝 (Google Colab)
`data/sft/train.jsonl`을 Colab에 올리고 `train/finetune_unsloth.py`를 셀 단위로 실행합니다.
생성된 `.gguf`를 내려받아 Ollama에 등록합니다.

```bash
ollama create text2sql-ft -f models/Modelfile
python scripts/predict.py --model text2sql-ft --tag ft-3b
python scripts/evaluate.py outputs/preds_ft-3b.jsonl
python scripts/compare.py outputs/preds_base-3b_eval.jsonl outputs/preds_ft-3b_eval.jsonl
```

### 4. API 서버
```bash
set TEXT2SQL_MODEL=text2sql-ft
uvicorn app.main:app --reload
```
`http://localhost:8000/docs`에서 테스트할 수 있습니다.

## 설계 메모

- **보안은 DB 계층에서 처리**: "DROP 포함 여부" 같은 문자열 검사는 우회가 쉽습니다. 그래서 SQLite를 읽기 전용으로 열고, `set_authorizer`로 SELECT/READ 외 모든 동작(PRAGMA, ATTACH 포함)을 거부하며, 실행 시간도 제한합니다.
- **문자열 비교 대신 실행 결과 비교**: `WHERE city = 'Seoul'`과 `WHERE city IN ('Seoul')`은 같은 답입니다. 정답 판정은 결과 행을 비교합니다.
- **응답 부분만 학습**: `train_on_responses_only`로 SQL 토큰에만 손실을 계산합니다.

## 로드맵

- [x] 베이스라인 측정 (zero-shot)
- [ ] 베이스라인 측정 (예시 행 포함)
- [x] QLoRA 파인튜닝 및 비교
- [x] 오류 분석: JOIN·GROUP BY·중첩 쿼리 등 유형별 실패 사례 정리
- [ ] **한국어 확장**: 가상 쇼핑몰 DB + 직접 만든 한국어 질문 평가셋(100개 이상)
- [x] 실행 오류 시 에러 메시지를 모델에 다시 주는 self-correction 루프
- [ ] self-correction 개선: 컬럼 목록 힌트, 재시도 temperature
- [ ] 웹 UI, Docker Compose
