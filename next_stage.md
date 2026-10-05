# 인수인계: 다음 작업 (next stage)

> 다른 컴퓨터에서 이 프로젝트를 이어서 작업하기 위한 문서입니다.
> 사람이 읽어도, AI 코딩 도우미(Claude Code 등)에게 그대로 건네도 이해할 수 있게 썼습니다.
> 작성 시점: 2026-10-05, 마지막 커밋 `a0a28a6 update v2` 이후 README·문서 갱신분까지 커밋 완료.

---

## 0. 한 줄 요약

로컬 3B 모델(Qwen2.5-Coder-3B)을 QLoRA로 파인튜닝한 Text-to-SQL 포트폴리오입니다. 실험, 평가, 데모 화면(영수증 프린터 UI), Docker 배포까지 끝났습니다. 남은 핵심 과제는 **v3 학습**입니다. v1은 JOIN을 너무 적게, v2는 너무 많이 하는 문제가 있어서, 그 균형을 잡는 학습이에요.

---

## 1. 지금까지의 결과 (숫자는 모두 실측)

| 평가 | 베이스라인 | v1 (Spider 학습) | v2 (+한국어 다중 JOIN) |
|---|---|---|---|
| Spider dev 1,034문제 (영어) | 61.8% | **73.4%** | 73.1% |
| 직접 만든 한국어 쇼핑몰 100문제 | **71%** | 66% | 68% |
| └ JOIN 2개 이상 (14문제) | **9** | 2 | 4 |
| 외부 LLM 4곳이 만든 한국어 118문항 | **73.7%** | 61.0% | 61.9% |
| └ JOIN 0개 (59) | **90%** | 86% | 81% |
| └ JOIN 1개 (18) | **83%** | 78% | 61% |
| └ JOIN 2개 이상 (41) | **46%** | 17% | 34% |

- **자동수정(self-correction)**: Spider에서 +1.0%p (73.4 → 74.4). 오류를 보고도 같은 SQL을 반복하는 비율이 40~65%라 효과가 작습니다. 컬럼 목록 힌트와 재샘플링은 효과가 없었습니다.
- **핵심 발견**:
  - v1은 Spider식 "짧게 쓰기" 버릇 때문에 중간 테이블(`order_items`)을 건너뜁니다.
  - v2는 그걸 고쳤지만 이번엔 **필요 없는 JOIN을 붙입니다.** 외부 질문에서 v1 → v2로 JOIN 2개 이상은 새로 맞음 10 / 새로 틀림 3, JOIN 0~1개는 새로 맞음 3 / 새로 틀림 9였어요.
  - 예: "브랜드별 상품 수"에서 `products`만 쓰면 되는데 `categories`를 붙이고 거기서 `brand`를 찾다가 실행 오류.
- 자세한 분석은 `README.md`에, 비전공자용 설명은 `structure_explanation.md`에 있습니다.

---

## 2. 새 컴퓨터에서 환경 만들기

### 2-1. Git에 없는 것 (직접 옮기거나 다시 만들어야 함)

| 항목 | 크기 | 없으면 생기는 일 | 구하는 방법 |
|---|---|---|---|
| `models/Qwen2.5-Coder-3B-Instruct.Q4_K_M.gguf` (v1) | 1.9GB | v1 모델 등록 불가 | USB 복사, 또는 Google Drive `내 드라이브/text2sql/gguf_out/`. 없으면 `structure_explanation.md` 4-1 (2)의 방법 B·C |
| `models/v2/Qwen2.5-Coder-3B-Instruct.Q4_K_M.gguf` (v2) | 1.9GB | v2 모델 등록 불가 | Drive `내 드라이브/text2sql/v2/gguf_out/` (LoRA는 `text2sql/v2/lora_adapter/`) |
| `outputs/` | 약 10MB | **비교·분석·화면 데이터 갱신 스크립트가 실패.** 다시 만들려면 예측을 전부 다시 돌려야 함 (수 시간) | **원래 컴퓨터에서 폴더째 복사 (강력 추천)** |
| `data/spider/` | 1.7GB | Spider 평가·학습 데이터 생성 불가 | https://yale-lily.github.io/spider 에서 `spider_data.zip`을 받아 `data/spider/`에 풀기 |
| `data/sft/` | 50MB | 학습 파일 없음 | `prepare_spider.py`, `make_train_v2.py`로 다시 생성 |
| `data/korean/database/`, `data/korean_train/` | 작음 | DB 없음 | 스크립트로 다시 생성 (고정 seed라 똑같이 만들어짐) |

`outputs/`의 주요 파일 (`*_eval.jsonl`이 채점 결과):

| 태그 | 내용 |
|---|---|
| `base-3b`, `ft-3b`, `ft-v2` | Spider 1,034문제 (베이스라인, v1, v2) |
| `base-3b-sc`, `ft-3b-sc`, `ft-3b-sc-hint`, `ft-3b-sc-hint-temp` | 자동수정 실험 |
| `ko-base-3b`, `ko-ft-3b`, `ko-ft-v2` | 직접 만든 한국어 100문제 |
| `ext-base-3b`, `ext-ft-3b`, `ext-ft-v2` | 외부 LLM 118문항 (`--tie-aware`로 채점) |

### 2-2. 설치 순서 (Windows 기준)

```bash
git clone https://github.com/dyj02056/local_LLM_build.git
cd local_LLM_build

# 파이썬 환경
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,plot]"
pytest                                   # 33개 통과해야 정상

# 데이터 (Spider는 먼저 data/spider/ 에 풀어 둘 것)
python scripts/prepare_spider.py
python scripts/build_shop_db.py
python scripts/prepare_korean.py
python scripts/build_korean_train_dbs.py
python scripts/gen_korean_train.py
python scripts/make_train_v2.py
python scripts/prepare_external.py

# AI 모델 (Ollama 설치 후, GGUF를 models/ 와 models/v2/ 에 넣은 뒤)
ollama pull qwen2.5-coder:3b
ollama create text2sql-ft -f models/Modelfile
ollama create text2sql-ft-v2 -f models/v2/Modelfile

# 화면
cd web
npm install
npm run build
cd ..
uvicorn app.main:app                     # http://localhost:8000
```

Docker로 실행하려면 `docker compose up -d --build`를 씁니다 (디스크 약 13GB 필요).

---

## 3. 다음 작업 목록 (추천 순서)

| 순서 | 작업 | 누가 | 시간 | 우선순위 |
|---|---|---|---|---|
| 1 | 화면에 외부 질문 결과 추가 | AI | 20분 | 높음 |
| 2 | README 다듬기 (요약 위, 세부는 접기) | AI | 20분 | 높음 |
| 3 | Docker 재시작으로 건강 검진 설정 적용 | 사용자 | 1분 | 낮음 |
| 4 | **v3 학습: JOIN 필요·불필요 균형** | AI + 사용자(Colab) | 약 6시간 | **가장 중요** |
| 5 | 오류 수정 대화 학습 (4번과 합칠 수 있음) | AI + 사용자 | +30분 | 중간 |
| 6 | 스키마에 예시 행 3개 실험 | AI | 약 2시간 | 중간 |
| 7 | 7B 모델 실험 | AI + 사용자 | 9시간 이상 | 낮음 |
| 8 | Hugging Face Hub에 모델 공개 | 사용자 + AI | 30분 | 중간 |
| 9 | GitHub 저장소 About, Topics, Pin | 사용자 | 10분 | 중간 |
| 10 | 프로젝트 종료 시 용량 정리 | AI(확인 후) | 10분 | 마지막 |

---

### 작업 1. 화면에 외부 질문 결과 추가 (20분)

- **목표**: 정산 리포트에 "외부 AI 질문 118문항" 구역을 추가합니다. 위 1장의 외부 질문 표(출처별 + JOIN 수별)와 "v1은 적게, v2는 많이 잇는다"는 해석을 넣어요. Z정산 요약에도 한두 줄 넣습니다.
- **수정할 파일**
  - `web/src/data/report.ts`: `external` 객체 추가. 숫자는 `python scripts/report_external.py`의 출력에서 가져옴
  - `web/src/components/ZReport.tsx`: `Segment` 하나 추가 (기존 "한국어 쇼핑몰 100문제" 구역과 같은 표 형식)
- **지켜야 할 디자인 규칙** (`DESIGN.md`, `.impeccable/surfaces/web-src-app-tsx.md`)
  - 빨간색(`thermal`)은 VOID, 오류, 나빠진 수치에만 씁니다.
  - 강조는 글자 크기가 아니라 2배 높이(`.dh`), 반전, 밑줄로 합니다.
  - 정산 리포트 오른쪽은 **하나로 이어진 테이프**입니다. 카드 여러 장으로 나누지 마세요.
- **확인**: `cd web && npx tsc --noEmit -p . && npm run build`, 데스크톱(1440px)과 모바일(390px)에서 화면 확인, 원하면 `npm run record`로 README GIF·스크린샷 다시 녹화 (앱이 8000번 포트에서 실행 중이어야 함)

### 작업 2. README 다듬기 (20분)

- **목표**: 면접관이 첫 화면에서 30초 안에 파악할 수 있게 합니다. 맨 위에는 GIF, 핵심 결과표, 스크린샷만 두고, 세부 분석(오류 분석, 자동수정 실험, v2, 외부 평가)은 `<details><summary>`로 접어 둡니다.
- **주의**: 숫자와 내용은 바꾸지 말고 배치만 바꿉니다. 한계와 실패한 실험도 지우지 않습니다 (프로젝트 원칙: "나쁜 결과도 똑같이 크게").

### 작업 3. Docker 재시작 (사용자, 1분)

`docker-compose.yml`의 Ollama 건강 검진 간격을 5초에서 30초로 바꿨습니다 (처음 켤 때만 2초 간격). `docker compose up -d`를 다시 실행하면 적용됩니다.

### 작업 4. v3 학습: JOIN 필요·불필요 균형 (가장 중요, 약 6시간)

**왜**: v1은 JOIN을 덜 하고, v2는 학습 데이터의 62%를 다중 JOIN으로 채운 탓에 JOIN을 더 합니다. v3은 "필요할 때만 잇는" 판단력을 가르치는 게 목표예요.

**데이터 설계** (`scripts/gen_korean_train.py`를 확장하거나 `gen_korean_train_v3.py`를 새로 만듦)

1. 기존 학습용 DB 4개(도서관 `library`, 병원 `hospital`, 학원 `academy`, 여행사 `travel`)를 그대로 씁니다. 평가용 쇼핑몰(`shop`)과 전자상거래 형태 DB는 **절대 쓰지 않습니다** (평가 누수 방지).
2. JOIN 수 비율을 외부 질문 분포에 맞춥니다: **0개 약 50%, 1개 약 15%, 2개 이상 약 35%** (현재 v2 데이터는 0개 17%, 1개 21%, 2개 이상 62%).
3. **대조 쌍 넣기**: 같은 DB에서 비슷한 말투인데 JOIN 필요 여부만 다른 질문을 짝지어 넣습니다.
   - "장르별 책 권수" (`books` + `genres`, JOIN 1개) ↔ "출간 연도별 책 권수" (`books`만, JOIN 0개)
   - "진료과별 처방 건수" (JOIN 3개) ↔ "제약사별 약 개수" (`drugs`만)
   - v2가 틀린 패턴과 같은 모양을 넣습니다. 한 테이블 안에 있는 컬럼(예: `brand`, `price`, `stock`)으로 묶는 질문을 일부러 많이 만들어요.
4. 템플릿 다양성을 늘립니다. 현재 70여 개 → 목표 120개 이상. 같은 템플릿에서 너무 많이 뽑지 않도록 템플릿당 상한(`cap`)을 낮춥니다.
5. (선택) 작업 5의 오류 수정 대화를 함께 섞습니다.

**실행 순서**

```bash
python scripts/gen_korean_train_v3.py      # 새로 만들 스크립트 -> data/korean_train/train_ko_v3.jsonl
python scripts/make_train_v2.py --korean data/korean_train/train_ko_v3.jsonl --out data/sft/train_v3.jsonl
```

- `train/finetune_unsloth.py` 셀 2의 `DATA_FILE` 사전에 `"v3": "data/sft/train_v3.jsonl"`을 추가하고 `RUN = "v3"`로 Colab 학습 (약 2.5~3시간). 결과는 Drive `text2sql/v3/`에 저장됩니다.
- GGUF를 `models/v3/`에 받고 `models/Modelfile`을 복사한 뒤 `ollama create text2sql-ft-v3 -f models/v3/Modelfile`
- 평가 (세 가지 모두 같은 방식으로):
  ```bash
  python scripts/predict.py --data data/korean/dev_ko.jsonl --model text2sql-ft-v3 --tag ko-ft-v3
  python scripts/evaluate.py outputs/preds_ko-ft-v3.jsonl --db-root data/korean/database
  python scripts/predict.py --data data/korean/dev_ext.jsonl --model text2sql-ft-v3 --tag ext-ft-v3
  python scripts/evaluate.py outputs/preds_ext-ft-v3.jsonl --db-root data/korean/database --tie-aware
  python scripts/predict.py --model text2sql-ft-v3 --tag ft-v3                  # Spider, 약 1시간 30분
  python scripts/evaluate.py outputs/preds_ft-v3.jsonl
  ```
- `scripts/report_external.py`와 화면(`MODEL_KEYS`, `MODELS`, `api.ts`의 `ModelKey`, `app/main.py`의 `MODELS`)에 v3를 추가합니다.

**성공 기준**: 외부 118문항에서 JOIN 2개 이상은 v2 수준(34%) 이상을 유지하면서, JOIN 0~1개는 v1 수준(86%, 78%)으로 회복. Spider는 73% 안팎 유지. 결과가 나쁘더라도 README에 그대로 기록합니다.

### 작업 5. 오류 수정 대화 학습 (작업 4와 합치기 추천)

- **목표**: 자동수정 때 "오류를 보고도 같은 SQL을 반복"하는 문제를 학습으로 해결합니다.
- **데이터**: 학습용 DB 4개에서 일부러 틀린 SQL(없는 컬럼, 잘못된 별칭, 중간 테이블 누락)을 만들고, 실행해서 얻은 실제 SQLite 오류 메시지와 함께 "틀린 SQL → 오류 메시지 → 고친 SQL" 대화를 만듭니다. 형식은 `src/text2sql/correct.py`의 `build_fix_messages()`와 똑같아야 합니다.
- **평가**: `scripts/self_correct.py --model text2sql-ft-v3 --src ft-v3 --tag ft-v3-sc`로 Spider 자동수정 효과와 "같은 SQL 반복" 비율을 v1(40%)과 비교합니다.

### 작업 6. 스키마에 예시 행 3개 넣기 (약 2시간, 학습 없음)

- 프롬프트에 테이블별 예시 행을 넣은 dev 파일을 만들고, 베이스라인으로 1,034문제를 평가합니다.
  ```bash
  python scripts/prepare_spider.py --sample-rows 3 --out-dir data/sft_rows
  python scripts/predict.py --data data/sft_rows/dev.jsonl --model qwen2.5-coder:3b --tag base-3b-rows
  python scripts/evaluate.py outputs/preds_base-3b-rows.jsonl
  python scripts/compare.py outputs/preds_base-3b_eval.jsonl outputs/preds_base-3b-rows_eval.jsonl
  ```
- 컬럼을 엉뚱한 테이블에서 찾는 오류(`no such column`)가 줄어드는지 봅니다. README 결과표의 "+ 예시 행 3개" 줄을 채웁니다.
- 참고: 학습 때와 다른 프롬프트를 파인튜닝 모델에 주면 성능이 떨어질 수 있으니 베이스라인만 평가합니다.

### 작업 7. 7B 모델 실험 (선택)

- `finetune_unsloth.py`의 `MODEL_NAME`을 `unsloth/Qwen2.5-Coder-7B-Instruct`로 바꿉니다. T4 메모리에 맞추려면 배치를 1로 줄이고 누적을 8로 늘려야 할 수 있어요.
- CPU 추론 시간이 2배 이상이라 Spider 평가가 3시간 이상 걸립니다.

### 작업 8. Hugging Face Hub에 모델 공개

- 사용자가 Hugging Face 계정과 토큰을 직접 만들어야 합니다. **토큰은 AI에게 입력시키지 말고 직접 로그인하세요** (`huggingface-cli login`).
- GGUF와 Modelfile을 올리면 다른 사람이 `ollama run hf.co/<계정>/<저장소>` 한 줄로 받아 쓸 수 있습니다. README에 사용법을 추가합니다.
- 모델 카드에는 학습 데이터(Spider 라이선스 CC BY-SA 4.0), 결과표, 한계(한국어 다중 JOIN 약점)를 적습니다.

### 작업 9. GitHub 저장소 꾸미기 (사용자)

- **Description**: `로컬 3B LLM을 QLoRA로 파인튜닝한 Text-to-SQL. Spider +11.6%p, 직접 만든 한국어 평가셋과 외부 LLM 질문으로 다중 JOIN 약점 검증`
- **Topics**: `text-to-sql`, `llm`, `qlora`, `fine-tuning`, `ollama`, `fastapi`, `react`
- 프로필에서 저장소를 **Pin**합니다.

### 작업 10. 프로젝트 종료 시 용량 정리

```bash
powershell -ExecutionPolicy Bypass -File scripts/cleanup.ps1          # 미리보기
powershell -ExecutionPolicy Bypass -File scripts/cleanup.ps1 -Apply   # 확인 후 실제 삭제
```

- 기본 삭제 대상: Docker(약 14GB), 이 프로젝트의 Ollama 모델, 다시 받을 수 있는 데이터, 설치 패키지
- `models/*.gguf`는 `-IncludeModels`를 줄 때만 지웁니다.
- 이 프로젝트와 무관한 Ollama 모델(`bge-m3`, `kanana-2-3b`)은 건드리지 않습니다.
- Docker Desktop은 안에서 지워도 가상 디스크가 줄지 않으므로, 설정의 **Clean / Purge data**로 공간을 돌려받습니다.
- Google Drive `text2sql/`은 `lora_adapter` 폴더만 남기고 GGUF는 지워도 됩니다.

---

## 4. 알아 둘 점 (작업하며 겪은 함정)

| 상황 | 내용 |
|---|---|
| 평가 공정성 | 학습 데이터에 평가용 `shop` DB나 쇼핑몰 형태 DB를 쓰지 않습니다. 평가 질문(`data/korean/questions.json`, `questions_external.json`)과 겹치는 질문은 `gen_korean_train.py`가 자동으로 뺍니다 |
| 정렬 동점 | 정답 SQL의 정렬에 동점이 있으면 순서가 여러 개 가능합니다. 새 질문셋은 `scripts/check_order_ties.py`로 검사하고, 동점이 있으면 `evaluate.py --tie-aware`로 채점합니다. 기본 채점은 엄격 모드라 기존 Spider 숫자와 비교할 수 있습니다 |
| 질문셋 검증 | 새 질문은 `prepare_korean.py` 같은 검사로 빈 결과, 정답 0, LIMIT 동점을 걸러야 합니다. 빈 결과나 0은 틀린 SQL도 우연히 맞힐 수 있습니다 |
| CPU 경쟁 | 평가 중에는 Docker의 Ollama로 질문을 돌리지 마세요. 같은 CPU를 써서 응답 시간 기록이 부풀려집니다 (정답률은 영향 없음) |
| 평가 이어서 하기 | `predict.py`는 이미 만든 줄은 건너뛰고 이어서 실행합니다. 설정을 바꿔 다시 돌릴 때는 `--tag`를 바꾸거나 기존 파일을 지웁니다 |
| PowerShell 5.1 한글 | `.ps1` 파일은 **BOM이 있는 UTF-8**로 저장해야 한글이 깨지지 않습니다 (`cleanup.ps1`이 그렇게 저장됨) |
| Colab 업로드 위치 | Colab 파일 창은 이미 `/content` 안을 보여 줍니다. 거기서 `content` 폴더를 또 만들면 `/content/content/...`가 됩니다. 업로드 셀(`files.upload()`)을 쓰는 게 안전합니다 |
| Colab 결과 덮어쓰기 | `RUN` 값을 바꾸지 않고 다시 학습하면 Drive의 이전 결과를 덮어씁니다. 실행마다 `v3`, `v4`처럼 새 이름을 쓰세요 |
| Loss 비교 | 템플릿 데이터를 섞으면 Loss가 낮아지지만 실력이 좋아졌다는 뜻이 아닙니다. 판단은 항상 평가 정확도로 합니다 |
| 화면 데이터 | 화면의 숫자는 `web/src/data/report.ts`(손으로 관리)와 `scripts/export_demo_data.py`(카탈로그, Loss를 자동으로 내보냄)에서 옵니다. 결과가 바뀌면 둘 다 갱신하고 `npm run build`를 다시 합니다 |
| 브라우저 미리보기 | 앱 창이 가려져 있으면 `requestAnimationFrame`이 멈춥니다. 시간 지연에는 `setTimeout`을 씁니다 |

---

## 5. 작업 방식 (이 프로젝트 사용자와 일할 때)

- 사용자는 **비전공자 관점의 쉬운 설명**을 선호합니다. 명령어는 단계별로, 결과 해석은 **표와 비유**로 설명합니다.
- 오래 걸리는 작업은 **예상 종료 시각(몇 시 몇 분)** 을 알려 주고, 바뀌면 다시 알려 줍니다.
- **커밋은 사용자가 직접** 합니다. AI는 바뀐 파일 목록과 커밋 명령만 제안합니다.
- 결정이 필요한 부분(평가 문항 수정, 디자인 방향 등)은 AI가 임의로 정하지 않고 선택지를 보여 주고 확인받습니다.
- 좋은 결과든 나쁜 결과든 **숫자와 한계를 그대로** README에 기록합니다.
- 화면 작업은 `DESIGN.md`(영수증 프린터 디자인 체계)와 `PRODUCT.md`(사용자: 면접관·채용 담당자)를 따릅니다.

---

## 6. 주요 파일 위치

| 무엇 | 어디 |
|---|---|
| 결과와 분석 (포트폴리오 본문) | `README.md` |
| 비전공자용 설명, 모델 설치·GGUF 재생성 방법 | `structure_explanation.md` |
| Colab 학습 코드 | `train/finetune_unsloth.py` |
| 평가·비교 도구 | `scripts/predict.py`, `evaluate.py`, `compare.py`, `report_external.py` |
| 한국어 평가 질문 | `data/korean/questions.json` (직접 100개), `questions_external.json` (외부 118개, 원본은 `questions_external_<출처>.json`) |
| 외부 질문 생성 프롬프트 | `data/korean/questions_generation_prompt.md` |
| v2 학습 데이터 생성 | `scripts/build_korean_train_dbs.py`, `gen_korean_train.py`, `make_train_v2.py` |
| 화면 코드 | `web/src/` (`components/Receipt.tsx`, `ZReport.tsx`, `data/report.ts`) |
| 서버 | `app/main.py` (`/api/query`, `/api/health`, `/api/databases`) |
| 디자인 규칙 | `DESIGN.md`, `PRODUCT.md`, `.impeccable/` |
