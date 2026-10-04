# Local Text-to-SQL

자연어 질문을 SQL로 바꿔 실행해 주는 **로컬 LLM**입니다.
오픈소스 코드 모델(Qwen2.5-Coder)을 Spider 데이터셋으로 QLoRA 파인튜닝하고, Ollama로 로컬에서 서빙합니다.

```
질문 ─▶ FastAPI ─▶ 스키마 + 질문 프롬프트 ─▶ Ollama(파인튜닝 모델) ─▶ SQL
                                                                  │
          결과 ◀── 읽기 전용 · 권한 제한 · 타임아웃이 걸린 SQLite 실행 ◀┘
```

## 결과

Spider dev 세트 실행 정확도(Execution Accuracy)입니다. 실험을 진행하면서 채웁니다.
현재 수치는 dev 앞 200문제(DB 4개: car_1, concert_singer, pets_1, flight_2) 기준입니다.

| 모델 | 방식 | EX | SQL 오류율 | 평균 지연(CPU) |
|---|---|---|---|---|
| Qwen2.5-Coder-3B | zero-shot | 49.5% | 28.0% | 6.43s |
| Qwen2.5-Coder-3B | + 예시 행 3개 | - | - | - |
| Qwen2.5-Coder-3B | QLoRA 파인튜닝 | - | - | - |

## 구조

```
src/text2sql/
  prompt.py      학습·추론 공통 프롬프트 + 모델 출력에서 SQL 추출
  schema.py      SQLite → CREATE TABLE 스키마 텍스트
  executor.py    안전한 SQL 실행 (읽기 전용 + authorizer + 타임아웃)
  evaluate.py    실행 정확도 계산
  llm.py         Ollama 클라이언트
scripts/
  prepare_spider.py   Spider → chat 형식 JSONL
  predict.py          모델로 dev 세트 SQL 생성 (중단 후 이어서 실행 가능)
  evaluate.py         정확도·오류율·지연시간 집계
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
ollama create text2sql-ft -f Modelfile
python scripts/predict.py --model text2sql-ft --tag ft-3b --limit 200
python scripts/evaluate.py outputs/preds_ft-3b.jsonl
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

- [ ] 베이스라인 측정 (zero-shot, 예시 행 포함)
- [ ] QLoRA 파인튜닝 및 비교
- [ ] 오류 분석: JOIN·GROUP BY·중첩 쿼리 등 유형별 실패 사례 정리
- [ ] **한국어 확장**: 가상 쇼핑몰 DB + 직접 만든 한국어 질문 평가셋(100개 이상)
- [ ] 실행 오류 시 에러 메시지를 모델에 다시 주는 self-correction 루프
- [ ] 웹 UI, Docker Compose
