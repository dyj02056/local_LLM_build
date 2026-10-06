# 인수인계: 다음 작업 (next stage)

> 다른 컴퓨터나 새 채팅에서 이 프로젝트를 이어서 작업하기 위한 문서입니다.
> 사람이 읽어도, AI 코딩 도우미(Claude Code 등)에게 그대로 건네도 이해할 수 있게 썼습니다.
> 작성 시점: 2026-10-07 오전. 마지막 커밋 `712302d Create loss_table_v3.txt`.
> 커밋 안 된 변경: `train/finetune_kaggle.py`, `train/finetune_kaggle.ipynb` (nan 대응 수정, 아래 4장 참고)

---

## 0. 한 줄 요약

로컬 3B 모델(Qwen2.5-Coder-3B)을 QLoRA로 파인튜닝한 Text-to-SQL 포트폴리오입니다. **v3 학습(JOIN 필요·불필요 균형)이 Kaggle에서 방금 정상 완료**됐습니다. 남은 핵심 과제는 **v3 결과물을 받아 평가하고 README와 화면에 반영하는 것**입니다.

---

## 1. 지금까지의 결과 (숫자는 모두 실측)

| 평가 | 베이스라인 | v1 (Spider 학습) | v2 (+한국어 다중 JOIN) | v3 |
|---|---|---|---|---|
| Spider dev 1,034문제 (영어) | 61.8% | **73.4%** | 73.1% | 평가 전 |
| 직접 만든 한국어 쇼핑몰 100문제 | **71%** | 66% | 68% | 평가 전 |
| └ JOIN 2개 이상 (14문제) | **9** | 2 | 4 | 평가 전 |
| 외부 LLM 4곳이 만든 한국어 118문항 | **73.7%** | 61.0% | 61.9% | 평가 전 |
| └ JOIN 0개 (59) | **90%** | 86% | 81% | 평가 전 |
| └ JOIN 1개 (18) | **83%** | 78% | 61% | 평가 전 |
| └ JOIN 2개 이상 (41) | **46%** | 17% | 34% | 평가 전 |

추가 실험 (학습 없음):

| 실험 | 결과 |
|---|---|
| 자동수정(self-correction) | Spider +1.0%p (v1 73.4 → 74.4), 베이스라인 +0.8%p. 오류를 보고도 같은 SQL을 반복하는 비율이 40~65%라 효과가 작음 |
| **스키마에 예시 행 3개 (2026-10-06 완료)** | 베이스라인 **61.8% → 65.7% (+3.9%p)**, `no such column` 129 → 111, 새로 맞음 69 / 새로 틀림 29 (McNemar p < 0.001). README에 반영 완료 |

- 예시 행 실험에서 발견한 점: `flight_2` DB의 도시 값에는 실제로 끝 공백이 있습니다(`'Aberdeen '`). 그래서 예시 행을 보고 공백까지 쓴 모델이 오히려 맞는데도, 정답 SQL이 빈 결과를 내서 오답 처리됩니다. README에 기록해 두었습니다.
- v1은 중간 테이블(`order_items`)을 건너뛰고, v2는 필요 없는 JOIN을 붙입니다. v3는 이 균형을 잡으려는 학습입니다.

---

## 2. 완료된 작업 (next_stage 초판 대비)

| # | 작업 | 상태 | 결과물 |
|---|---|---|---|
| 1 | 화면에 외부 질문 결과 추가 | ✅ | `ZReport.tsx`, `report.ts`의 `external` |
| 2 | README 다듬기 (요약은 위로, 세부는 접기) | ✅ | `<details>` 9개 |
| 3 | Docker 건강 검진 간격 | ✅ 설정 반영 | `docker-compose.yml` (30초, 시작할 때만 2초) |
| 4 | **v3 학습 데이터** | ✅ | `scripts/gen_korean_train_v3.py` → `data/korean_train/train_ko_v3.jsonl` (1,000개) → `data/sft/train_v3.jsonl` (10,659개) |
| 4 | **v3 학습** | ✅ **학습 완료, 다운로드·평가 전** | Kaggle 노트북 `v3_training` Version 3 |
| 5 | 오류 수정 대화 학습 | 🟡 준비만 됨 | `scripts/gen_fix_dialogs.py`, Kaggle·Colab 코드의 `v4` 항목. **사용자 결정: v3(균형만)를 먼저 따로 평가한 뒤 v4로 진행** |
| 6 | 스키마에 예시 행 3개 | ✅ | 위 1장 표, `outputs/compare_base_vs_rows.md` |
| 7 | 7B 모델 실험 | ⬜ | 선택 작업 |
| 8 | Hugging Face 공개 | 🟡 모델 카드 초안만 | `docs/huggingface_model_card.md` |
| 9 | GitHub About, Topics, Pin | ❓ | 사용자가 GitHub 웹에서 직접 |
| 10 | 용량 정리 | ⬜ | 맨 마지막 |

### v3 학습 데이터 검사 결과

| 항목 | 목표 | 결과 |
|---|---|---|
| JOIN 0 / 1 / 2개 이상 | 50 / 15 / 35% | 500 / 150 / 350 (정확히 일치) |
| 템플릿 | 120개 이상 | 169개 (v2 71 + 새로 98), 실제 사용 166개, 템플릿당 최대 20개 |
| DB | 학습용 4개만 | library 303, hospital 261, academy 227, travel 209 (`shop` 없음) |
| 평가 질문과 겹침, 중복 | 0 | 0, 0 |
| 정답 SQL 실행 | 오류·빈 결과 없음 | 1,000개 모두 정상 |

재생성: `python scripts/gen_korean_train_v3.py`, 이어서 `python scripts/make_train_v2.py --korean data/korean_train/train_ko_v3.jsonl --out data/sft/train_v3.jsonl` (고정 seed라 똑같이 만들어짐)

---

## 3. v3 학습 경과 (Kaggle) — README에 쓸 만한 경험

Colab 무료 사용량이 바닥나서 **Kaggle Notebooks**(주 약 30시간 GPU, T4)로 옮겼습니다.

| 시도 | Kaggle 버전 | 결과 |
|---|---|---|
| 1차 | Version 1 (2시간 20분) | ❌ **step 80부터 끝까지 Loss가 nan.** 모델 파일은 정상처럼 보였지만, v3 학습 문제 30개를 냈을 때 v3 22개 / v2 26개를 맞혀 사실상 학습되지 않은 것을 확인하고 폐기함 |
| 시험 | Version 2 (20분, `TEST_STEPS = 150`) | ✅ step 150까지 nan 없음 |
| 2차 | Version 3 (약 2시간 35분) | ✅ **1,323단계 완료, loss 132줄 중 nan 0개.** 0.381에서 시작해 마지막 0.056 (v2 마지막 0.056과 비슷) |

- **원인**: 새 Unsloth(2026.9.14)가 자동으로 켠 **padding-free** 기능 (`Padding-free auto-enabled` 로그)으로 추정됩니다. 끄고 나서 같은 구간(step 70~80)을 정상 통과했어요. 1차와 2차의 loss는 step 70까지 소수 넷째 자리까지 같았습니다.
- **대가**: padding-free를 끄면 1단계당 약 5.5초에서 6.7초로 느려집니다.
- **환경**: unsloth 2026.9.14, transformers 5.5.0, trl 0.24.0, torch 2.11.0+cu128, Python 3.13, Tesla T4 1장
- **교훈**: 모델이 답을 내는 것만으로는 학습됐다고 볼 수 없습니다. loss 기록과 "학습 데이터 문제를 맞히는지"로 확인해야 해요.

---

## 4. 바로 다음 할 일 (순서대로)

### 4-0. 커밋 (사용자)

nan 대응으로 고친 Kaggle 학습 코드가 아직 커밋 전입니다.

```bash
git add train/finetune_kaggle.py train/finetune_kaggle.ipynb
git commit -m "fix Kaggle training: disable padding-free, nan guard, test mode"
```

고친 내용: `padding_free=False`, 10단계마다 loss를 로그에 출력하는 `Monitor` 콜백, nan이 나오면 즉시 중단하고 저장하지 않음, `TEST_STEPS`(앞부분만 시험 실행), 버전 출력.
노트북 파일 `.ipynb`는 `.py`를 셀(`# %%`) 단위로 나눠 만든 것입니다. `.py`를 고치면 같은 방식으로 `.ipynb`도 다시 만들어야 합니다.

### 4-1. v3 결과물 다운로드 (사용자)

Kaggle → 노트북 `v3_training` → **Version 3** → **Output** 탭 (Version 1 Output은 실패한 학습이니 받지 마세요)

| 받을 파일 | 둘 곳 | 비고 |
|---|---|---|
| `v3/gguf_out/Qwen2.5-Coder-3B-Instruct.Q4_K_M.gguf` (1.93GB) | `models/v3/` (같은 이름) | 필수 |
| `v3/loss_table.txt` | `loss_table/loss_table_v3.txt`로 **덮어쓰기** | ⚠️ 지금 커밋된 `loss_table_v3.txt`는 **1차 실패본(nan 125줄)** 입니다. 반드시 바꾸고 다시 커밋하세요 |
| `v3/lora_adapter/` (약 130MB) | Google Drive `text2sql/v3/` | 보관용 (HF 공개, GGUF 재생성에 필요) |

- 실패본 v3 GGUF와 Ollama `text2sql-ft-v3` 모델은 이미 지웠습니다. 지금 `models/v3/`에는 `Modelfile`만 있어요.
- AI가 Kaggle을 확인하려면 앱의 Browser 패널에 사용자가 직접 로그인해야 합니다 (패널을 다시 열면 로그인이 풀리기도 함). 실행 중 로그는 Version History → `⋯` → **View logs**에 있습니다.

### 4-2. 등록과 학습 여부 확인 (AI, 10분)

```bash
python -c "import sys;L=open('loss_table/loss_table_v3.txt').read().split();print('nan' in L)"   # False여야 함
ollama create text2sql-ft-v3 -f models/v3/Modelfile
```

**학습 여부 판별**: `data/korean_train/train_ko_v3.jsonl` 중 v2 학습 데이터(`train_ko.jsonl`)에 없는 질문(510개)에서 seed 0으로 30개를 뽑습니다. 이걸 `text2sql-ft-v3`와 `text2sql-ft-v2`에 temperature 0으로 묻고 실행 결과로 채점해요. 1차 실패본은 v3 22 / v2 26이었습니다. 제대로 학습됐다면 v3가 크게 앞서야 합니다 (스크립트는 저장하지 않았으니 새로 짜면 됩니다. 응답의 ```sql 블록을 벗겨 내고 SQLite로 실행해 정렬한 결과를 비교).

### 4-3. 평가 (AI, 약 2시간 10분)

```bash
python scripts/predict.py --data data/korean/dev_ko.jsonl --model text2sql-ft-v3 --tag ko-ft-v3
python scripts/evaluate.py outputs/preds_ko-ft-v3.jsonl --db-root data/korean/database
python scripts/predict.py --data data/korean/dev_ext.jsonl --model text2sql-ft-v3 --tag ext-ft-v3
python scripts/evaluate.py outputs/preds_ext-ft-v3.jsonl --db-root data/korean/database --tie-aware
python scripts/predict.py --model text2sql-ft-v3 --tag ft-v3                  # Spider, 약 1시간 30분
python scripts/evaluate.py outputs/preds_ft-v3.jsonl
python scripts/compare.py outputs/preds_ft-v2_eval.jsonl outputs/preds_ft-v3_eval.jsonl
python scripts/compare.py outputs/preds_ext-ft-v2_eval.jsonl outputs/preds_ext-ft-v3_eval.jsonl
```

- Windows 콘솔 한글 깨짐 방지: `PYTHONIOENCODING=utf-8` (Git Bash에서는 `export PYTHONIOENCODING=utf-8`)
- 평가 중에는 Docker의 Ollama로 질문하지 마세요 (응답 시간 기록이 부풀려짐).

**성공 기준**: 외부 118문항에서 JOIN 2개 이상은 v2 수준(34%) 이상을 유지하면서 JOIN 0개·1개는 v1 수준(86%, 78%)으로 회복. Spider는 73% 안팎 유지. 결과가 나쁘더라도 README에 그대로 기록합니다.

### 4-4. 반영 (AI, 약 1시간)

- `scripts/report_external.py`에 v3 추가
- 화면: `web/src/data/report.ts` 숫자, `MODEL_KEYS`·`MODELS`, `web/src/api.ts`의 `ModelKey`, `app/main.py`의 `MODELS`. 이어서 `python scripts/export_demo_data.py`를 실행하고 `cd web && npx tsc --noEmit -p . && npm run build`
- Loss 그래프: `export_demo_data.py`는 지금 `loss_table.txt`, `loss_table_v2.txt`만 읽으니 v3 추가. `docs/loss_compare.png`도 v3를 넣어 다시 그림 (`plot_loss.py`는 파일을 인자로 받음)
- README: 결과표에 v3 열, "v3" 접기 항목 (데이터 설계, 결과, **3장의 Kaggle nan 경험**), 로드맵 체크, 실행 방법에 Kaggle 경로 추가
- `docs/huggingface_model_card.md`: 결과에 따라 올릴 모델(v1/v2/v3)을 정함

### 4-5. 그다음 후보

| 작업 | 내용 |
|---|---|
| v4 (작업 5) | `python scripts/gen_fix_dialogs.py` → `make_train_v2.py --korean data/korean_train/train_ko_v3.jsonl --extra data/korean_train/fix_dialogs.jsonl --out data/sft/train_v4.jsonl`. Kaggle 셀 2에서 `RUN = "v4"`, 먼저 `TEST_STEPS = 150`으로 시험. 평가: `scripts/self_correct.py --model text2sql-ft-v4 --src ft-v4 --tag ft-v4-sc`로 "같은 SQL 반복" 비율을 v1(40%)과 비교 |
| 예시 행 + 학습 | 예시 행이 베이스라인에 +3.9%p였으니, 학습 데이터도 `--sample-rows 3`으로 만들어 학습하는 실험을 해 볼 만함 (`data/sft_rows/train.jsonl`이 이미 생성돼 있음) |
| 8 | Hugging Face 공개 (토큰은 사용자가 `huggingface-cli login`으로 직접) |
| 10 | 프로젝트 종료 시 `scripts/cleanup.ps1` |

---

## 5. Kaggle 사용법 요약 (학습할 때마다)

| 단계 | 방법 |
|---|---|
| 데이터 | Create → New Dataset → `train_vN.jsonl` 업로드 (Private). 노트북 오른쪽 Input → Add Input으로 연결. 코드가 `/kaggle/input` 아래에서 파일 이름으로 찾음 |
| 노트북 | 기존 노트북 `v3_training`에서 Edit → File → Import Notebook → `train/finetune_kaggle.ipynb` |
| 설정 | Accelerator **GPU T4 x2** (코드가 1장만 씀), Internet **On**. GPU를 쓰려면 전화번호 인증이 필요 |
| 시험 | 셀 2에서 `TEST_STEPS = 150` → Save Version → **Save & Run All**. 약 20분. 로그에 `시험 실행 정상 종료`가 나와야 함 |
| 본 학습 | 셀 2에서 `TEST_STEPS = 0` → Save & Run All. 약 2시간 50분 (GGUF 포함) |
| 주의 | 편집 화면에서 직접 돌리면 20분 동안 입력이 없을 때 끊김 → 반드시 Save & Run All. 편집 세션이 켜져 있으면 GPU 시간이 계속 줄어드니 전원 버튼으로 끄기. 버전은 삭제할 수 없음 (이름 변경만 가능) |
| 결과 | Version → Output 탭. `v3/` 폴더만 받으면 됨 (`huggingface_tokenizers_cache`, `unsloth_compiled_cache`는 임시 파일) |

Colab용 `train/finetune_unsloth.py`에는 nan 대응이 들어가 있지 않습니다. 다시 Colab을 쓴다면 같은 수정(`padding_free=False`, Monitor)을 옮겨야 해요.

---

## 6. 새 컴퓨터에서 환경 만들기

### 6-1. Git에 없는 것

| 항목 | 크기 | 구하는 방법 |
|---|---|---|
| `models/*.gguf` (v1), `models/v2/*.gguf` | 각 1.9GB | Google Drive `text2sql/gguf_out/`, `text2sql/v2/gguf_out/` |
| `models/v3/*.gguf` | 1.9GB | Kaggle `v3_training` Version 3 Output (4-1) |
| `outputs/` | 약 10MB | **원래 컴퓨터에서 폴더째 복사 (강력 추천).** 다시 만들려면 예측을 전부 다시 돌려야 함 (수 시간) |
| `data/spider/` | 1.7GB | https://yale-lily.github.io/spider 의 `spider_data.zip` |
| `data/sft/`, `data/sft_rows/`, `data/korean*/` | 작음~50MB | 아래 스크립트로 재생성 |

`outputs/` 주요 태그 (`*_eval.jsonl`이 채점 결과):

| 태그 | 내용 |
|---|---|
| `base-3b`, `ft-3b`, `ft-v2` | Spider 1,034문제 (베이스라인, v1, v2) |
| `base-3b-rows` | Spider, 베이스라인 + 예시 행 3개 |
| `base-3b-sc`, `ft-3b-sc`, `ft-3b-sc-hint`, `ft-3b-sc-hint-temp` | 자동수정 실험 |
| `ko-base-3b`, `ko-ft-3b`, `ko-ft-v2` | 직접 만든 한국어 100문제 |
| `ext-base-3b`, `ext-ft-3b`, `ext-ft-v2` | 외부 LLM 118문항 (`--tie-aware`) |

### 6-2. 설치 순서 (Windows)

```bash
git clone https://github.com/dyj02056/local_LLM_build.git
cd local_LLM_build
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,plot]"
pytest

python scripts/prepare_spider.py
python scripts/prepare_spider.py --sample-rows 3 --out-dir data/sft_rows
python scripts/build_shop_db.py
python scripts/prepare_korean.py
python scripts/build_korean_train_dbs.py
python scripts/gen_korean_train.py
python scripts/make_train_v2.py
python scripts/gen_korean_train_v3.py
python scripts/make_train_v2.py --korean data/korean_train/train_ko_v3.jsonl --out data/sft/train_v3.jsonl
python scripts/prepare_external.py

ollama pull qwen2.5-coder:3b
ollama create text2sql-ft -f models/Modelfile
ollama create text2sql-ft-v2 -f models/v2/Modelfile
ollama create text2sql-ft-v3 -f models/v3/Modelfile

cd web && npm install && npm run build && cd ..
uvicorn app.main:app                     # http://localhost:8000
```

---

## 7. 알아 둘 점 (작업하며 겪은 함정)

| 상황 | 내용 |
|---|---|
| **Kaggle nan** | 새 Unsloth의 padding-free 자동 활성화로 step 80부터 nan이 났습니다. `finetune_kaggle.py`에서 끔. Kaggle 로그에는 학습 진행 표가 안 보이므로 Monitor 콜백이 loss를 직접 출력합니다 |
| **학습 확인** | GGUF가 답을 낸다고 학습된 게 아닙니다. loss 기록(nan 여부)과 학습 데이터 문제 판별(4-2)로 확인하세요 |
| 평가 공정성 | 학습 데이터에 평가용 `shop` DB나 쇼핑몰 형태 DB를 쓰지 않습니다. 평가 질문과 겹치는 질문은 생성 스크립트가 자동으로 뺍니다 |
| 정렬 동점 | 새 질문셋은 `scripts/check_order_ties.py`로 검사하고, 동점이 있으면 `evaluate.py --tie-aware`로 채점 |
| 예시 행 프롬프트 | 파인튜닝 모델에는 학습 때와 같은 프롬프트만 줍니다. 예시 행은 베이스라인에만 적용했습니다 |
| CPU 경쟁 | 평가 중에는 Docker의 Ollama로 질문하지 마세요 |
| 평가 이어서 하기 | `predict.py`는 이미 만든 줄을 건너뜁니다. 설정을 바꾸면 `--tag`를 바꾸거나 기존 파일을 지우세요 |
| 한글 출력 | 콘솔 한글이 깨지면 `PYTHONIOENCODING=utf-8`. `.ps1`은 BOM 있는 UTF-8로 저장 |
| 실행 이름 | Colab은 `RUN`이 같으면 Drive 결과를 덮어씁니다. Kaggle은 버전마다 따로 남지만, 실패한 버전도 지울 수 없으니 이름을 바꿔 표시하세요 |
| Loss 비교 | 템플릿 데이터를 섞으면 Loss가 낮아지지만 실력이 좋아졌다는 뜻은 아닙니다. 판단은 항상 평가 정확도로 합니다 |
| 화면 데이터 | `web/src/data/report.ts`(손으로 관리)와 `scripts/export_demo_data.py`(자동). 결과가 바뀌면 둘 다 갱신하고 `npm run build` |
| 브라우저 미리보기 | 앱 창이 가려지면 `requestAnimationFrame`이 멈춥니다. 시간 지연에는 `setTimeout`을 씁니다 |

---

## 8. 작업 방식 (이 프로젝트 사용자와 일할 때)

- 사용자는 **비전공자 관점의 쉬운 설명**을 선호합니다. 명령어와 클릭 순서는 단계별로, 결과 해석은 **표와 비유**로 설명합니다.
- 오래 걸리는 작업은 **예상 종료 시각(몇 시 몇 분)** 을 알려 주고, 바뀌면 다시 알려 줍니다.
- **커밋은 사용자가 직접** 합니다. AI는 바뀐 파일 목록과 커밋 명령만 제안합니다.
- 결정이 필요한 부분은 AI가 임의로 정하지 않고 선택지를 보여 주고 확인받습니다.
- 좋은 결과든 나쁜 결과든 **숫자와 한계를 그대로** README에 기록합니다.
- 화면 작업은 `DESIGN.md`(영수증 프린터 디자인 체계)와 `PRODUCT.md`(사용자: 면접관·채용 담당자)를 따릅니다.

---

## 9. 주요 파일 위치

| 무엇 | 어디 |
|---|---|
| 결과와 분석 (포트폴리오 본문) | `README.md` |
| 비전공자용 설명, GGUF 재생성 방법 | `structure_explanation.md` |
| 학습 코드 | `train/finetune_kaggle.py` / `.ipynb` (Kaggle, 현재 사용), `train/finetune_unsloth.py` (Colab) |
| 학습 데이터 생성 | `scripts/gen_korean_train_v3.py`(v3), `gen_korean_train.py`(v2), `gen_fix_dialogs.py`(v4), `make_train_v2.py`(Spider와 합치기) |
| 평가·비교 도구 | `scripts/predict.py`, `evaluate.py`, `compare.py`, `report_external.py`, `self_correct.py` |
| Loss 기록 | `loss_table/loss_table.txt`(v1), `loss_table_v2.txt`, `loss_table_v3.txt`(**실패본, 교체 필요**) |
| 한국어 평가 질문 | `data/korean/questions.json` (직접 100개), `questions_external.json` (외부 118개) |
| 모델 카드 초안 | `docs/huggingface_model_card.md` |
| 화면 코드 | `web/src/` (`components/Receipt.tsx`, `ZReport.tsx`, `data/report.ts`) |
| 서버 | `app/main.py` |
| 디자인 규칙 | `DESIGN.md`, `PRODUCT.md`, `.impeccable/` |
