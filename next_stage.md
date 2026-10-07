# 인수인계: 다음 작업 (next stage)

> 다른 컴퓨터나 새 채팅에서 이 프로젝트를 이어서 작업하기 위한 문서입니다.
> 사람이 읽어도, AI 코딩 도우미(Claude Code 등)에게 그대로 건네도 이해할 수 있게 썼습니다.
> 작성 시점: 2026-10-07 낮 12시 반. v3 평가와 반영까지 끝난 상태입니다 (커밋은 사용자가 직접, 4-0 참고).

---

## 0. 한 줄 요약

로컬 3B 모델(Qwen2.5-Coder-3B)을 QLoRA로 파인튜닝한 Text-to-SQL 포트폴리오입니다. **v3(JOIN 필요·불필요 균형)를 평가해 README와 화면에 반영했습니다.** 외부 질문 61.0% → 69.5%로 v1·v2의 시소에서 벗어났지만 베이스라인(73.7%)은 아직 못 넘었습니다. 다음 후보는 **베이스라인 + 예시 행의 한국어 측정**, 그 결과에 따라 **v4(예시 행 포함 학습)** 입니다 (4장).

---

## 1. 지금까지의 결과 (숫자는 모두 실측)

| 평가 | 베이스라인 | v1 (Spider 학습) | v2 (+한국어 다중 JOIN) | v3 (+JOIN 균형) |
|---|---|---|---|---|
| Spider dev 1,034문제 (영어) | 61.8% | **73.4%** | 71.9%† | 72.1%† |
| 직접 만든 한국어 쇼핑몰 100문제 | **70%** | 67% | 67% | 67% |
| └ JOIN 2개 이상 (14문제) | **8** | 2 | 5 | 4 |
| 외부 LLM 4곳이 만든 한국어 118문항 | **73.7%** | 61.0% | 61.0% | 69.5% |
| └ JOIN 0개 (59) | **90%** | 86% | 81% | **90%** |
| └ JOIN 1개 (18) | **94%** | 78% | 72% | 78% |
| └ JOIN 2개 이상 (41) | **41%** | 17% | 27% | 37% |
| └ SQL 오류율 | **8.5%** | 21.2% | 25.4% | 14.4% |

**재측정 (2026-10-07)**: 한국어 두 평가는 네 모델을 모두 이 컴퓨터(Ollama 0.34.2)에서 다시 잰 값입니다. 처음 컴퓨터와 1~3문제씩 다릅니다 (예: 100문제 베이스라인 71→70, v1 66→67, v2 68→67). Spider는 베이스라인·v1이 처음 측정값이고, †는 이 컴퓨터 값입니다. v2 Spider가 73.1% → 71.9%로 바뀌어 **Spider도 환경에 따라 1%p 정도 흔들립니다.** README에 같은 메모가 있습니다.

v3 판정 (4-3의 성공 기준):
- 외부 JOIN 2개 이상 v2 이상 유지 ✅ (27 → 37%), JOIN 0·1개 v1 수준 회복 ✅ (90%, 78%), Spider 유지 ✅ (같은 PC에서 v2 71.9 → v3 72.1, 새로 맞음 54 / 새로 틀림 51)
- v2 → v3 외부 질문: 새로 맞음 19 / 새로 틀림 9 (z ≈ 1.9). 베이스라인 → v3: 7 / 12 (z ≈ -1.1)
- 직접 만든 100문제는 v1·v2·v3 모두 67%로 구분 안 됨
- 학습 여부 확인 (`scripts/check_learned.py`, 30문제): v3 30 / v2 27 (실패본은 22 / 26)

**지금 쓸 모델을 고른다면**: 한국어 실무 DB는 베이스라인, 영어·단순 DB는 v1(+자동수정), 파인튜닝 모델 중 한국어·영어를 함께 쓸 거라면 v3. v2는 v3로 대체됨.

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
| 4 | **v3 학습** | ✅ | Kaggle 노트북 `v3_training` Version 3 → `models/v3/`, Ollama `text2sql-ft-v3` |
| 4 | **v3 평가·반영** | ✅ (2026-10-07) | README v3 항목, 화면 v3 버튼·열, `docs/loss_compare.png`, `structure_explanation.md` 6장 |
| 5 | 오류 수정 대화 학습 | 🟡 준비만 됨 | `scripts/gen_fix_dialogs.py`, Kaggle·Colab 코드의 `v4` 항목. v3 평가 후 **예시 행 학습보다 후순위로 제안함** (4장) |
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

v3 모델 키·Loss 그래프는 이미 커밋됐습니다 (`2a87159`). 남은 변경:

| 분류 | 파일 |
|---|---|
| 문서 | `README.md`, `structure_explanation.md`, `next_stage.md` |
| 화면 | `web/src/App.tsx`, `data/report.ts`, `data/korean_catalog.json`, `components/ZReport.tsx`, `PrinterPanel.tsx` |
| 스크립트 | `scripts/check_learned.py` (새 파일) |

```bash
git add -A
git commit -m "v3 evaluation: JOIN-balanced model, re-measured Korean results"
```

`git status`로 `outputs/`나 `models/*.gguf`가 섞이지 않았는지 먼저 확인하세요 (둘 다 `.gitignore` 대상이어야 함).

### 4-1. 남은 보관 작업 (사용자)

- v3 `lora_adapter/` (약 130MB)를 Google Drive `text2sql/v3/`에 올렸는지 확인 (HF 공개와 GGUF 재생성에 필요)
- Kaggle Version 1·3 로그를 `outputs/kaggle_v3_try1.log`, `kaggle_v3.log`로 저장 (Kaggle 정리 전에)

### 4-2. 베이스라인 + 예시 행으로 한국어 측정 (AI, 약 30분, 학습 없음) ← 추천 다음 단계

예시 행 3개는 Spider 베이스라인을 61.8% → 65.7%로 올렸지만 **한국어 평가에는 아직 적용해 본 적이 없습니다.** 한국어에서 베이스라인이 가장 강하므로, 여기에 예시 행을 더하면 "지금 쓸 모델"이 바뀔 수 있습니다.

- 할 일: `prepare_korean.py`, `prepare_external.py`에 `prepare_spider.py`와 같은 `--sample-rows` 옵션 추가 (`get_schema(db_path, n)` 재사용) → `dev_ko_rows.jsonl`, `dev_ext_rows.jsonl` 생성
- 측정: `predict.py --model qwen2.5-coder:3b --tag ko-base-3b-rows` / `ext-base-3b-rows`, 외부는 `evaluate.py --tie-aware`
- 비교: `compare.py outputs/preds_ext-base-3b_eval.jsonl outputs/preds_ext-base-3b-rows_eval.jsonl`
- 파인튜닝 모델에는 적용하지 않습니다 (학습 때와 다른 프롬프트라 불공정).

### 4-3. v4 후보: 예시 행을 넣은 학습 (4-2 결과가 좋으면)

- 데이터: v3 한국어 데이터에 예시 행을 붙인 버전 + `data/sft_rows/train.jsonl`(Spider, 이미 생성됨). `make_train_v2.py`와 `gen_korean_train_v3.py`에 `--sample-rows` 경로를 추가해야 함
- 학습: Kaggle 노트북 `v3_training` 재사용, `RUN = "v4"`, 먼저 `TEST_STEPS = 150`
- 확인: `scripts/check_learned.py --new-model text2sql-ft-v4 --old-model text2sql-ft-v3 ...`
- 평가: 예시 행 프롬프트로 세 평가셋. 비교 대상은 **베이스라인 + 예시 행** (같은 조건)
- 함께 고려: 학습률을 낮추거나 Spider 비중을 줄여 원래 모델의 감각을 덜 덮어쓰기, 다른 LLM으로 질문 말투를 다양하게 만들기

### 4-4. 그다음 후보

| 작업 | 내용 |
|---|---|
| 오류 수정 대화 학습 | `python scripts/gen_fix_dialogs.py` → `make_train_v2.py --korean data/korean_train/train_ko_v3.jsonl --extra data/korean_train/fix_dialogs.jsonl --out data/sft/train_v5.jsonl`. 자동수정 효과(+1%p)가 작아 예시 행 학습보다 후순위. 평가: `scripts/self_correct.py`로 "같은 SQL 반복" 비율을 v1(40%)과 비교 |
| 7B 모델 | 선택. CPU 응답이 2배 이상 느려지고 프로젝트 주제(작은 모델)와 거리가 있음 |
| 8 | Hugging Face 공개 (토큰은 사용자가 `huggingface-cli login`으로 직접). 올릴 모델: 한국어·영어를 함께 쓸 거라면 v3 |
| 10 | 프로젝트 종료 시 `scripts/cleanup.ps1` |
| Kaggle 정리 | **삭제 전 확인**: v3 GGUF가 `models/v3/`에(✅), LoRA가 Drive `text2sql/v3/`에, Version 1·3 로그 저장(4-1). Dataset `text2sql-train-v3`는 언제 지워도 됨. v4를 할 거라면 **노트북은 남겨 두기** |

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
| `ft-v2`, `ft-v3` | Spider 1,034문제 (v2·v3, 이 컴퓨터). `base-3b`, `ft-3b`와 예시 행·자동수정 결과는 **처음 컴퓨터에만 있음** |
| `base-3b-rows` | Spider, 베이스라인 + 예시 행 3개 |
| `base-3b-sc`, `ft-3b-sc`, `ft-3b-sc-hint`, `ft-3b-sc-hint-temp` | 자동수정 실험 |
| `ko-base-3b`, `ko-ft-3b`, `ko-ft-v2`, `ko-ft-v3` | 직접 만든 한국어 100문제 (네 모델 모두 이 컴퓨터) |
| `ext-base-3b`, `ext-ft-3b`, `ext-ft-v2`, `ext-ft-v3` | 외부 LLM 118문항 (`--tie-aware`, 네 모델 모두 이 컴퓨터) |

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
| 평가·비교 도구 | `scripts/predict.py`, `evaluate.py`, `compare.py`, `report_external.py`, `self_correct.py`, `check_learned.py`(학습 여부 확인) |
| Loss 기록 | `loss_table/loss_table.txt`(v1), `loss_table_v2.txt`, `loss_table_v3.txt`(2차 성공본, nan 0개) |
| 한국어 평가 질문 | `data/korean/questions.json` (직접 100개), `questions_external.json` (외부 118개) |
| 모델 카드 초안 | `docs/huggingface_model_card.md` |
| 화면 코드 | `web/src/` (`components/Receipt.tsx`, `ZReport.tsx`, `data/report.ts`) |
| 서버 | `app/main.py` |
| 디자인 규칙 | `DESIGN.md`, `PRODUCT.md`, `.impeccable/` |
