# 인수인계: 다음 작업 (next stage)

> 다른 컴퓨터나 새 채팅에서 이 프로젝트를 이어서 작업하기 위한 문서입니다.
> 사람이 읽어도, AI 코딩 도우미(Claude Code 등)에게 그대로 건네도 이해할 수 있게 썼습니다.
> 작성 시점: 2026-10-07 17시. 마지막 커밋 `52d7dc5 update v3`. **이 문서 외에 커밋 안 된 코드 변경은 없습니다.**
> 이어서 할 컴퓨터는 지금과 다른 컴퓨터입니다. **시작 전에 6장(준비물)부터 보세요.**

---

## 0. 한 줄 요약

로컬 3B 모델(Qwen2.5-Coder-3B)을 QLoRA로 파인튜닝한 Text-to-SQL 포트폴리오입니다. v1 → v2 → v3 학습과 평가는 끝났고, 오늘(10/7) 오후에는 **학습 없이 정확도를 올리는 방법**(실행 결과 다수결, 7B 모델)을 측정했습니다.

- **7B 베이스라인이 한국어에서 가장 좋음**: 직접 만든 100문제 79%, 외부 118문항 86.4% (3B 베이스라인 70%, 73.7%)
- **다수결은 한국어에서는 효과, Spider에서는 손해**: 3B 5개 다수결이 한국어 78% / 80.5%로 올랐지만, Spider 3개 다수결은 69.8%로 v3 혼자(72.1%)보다 낮음. 원인은 "같은 모델 두 개가 한 편이 되는 것" (1-3)
- **남은 일**: Spider v1 측정 → Spider 5개 다수결 확인 → README·화면 반영 → 마무리 (4장)

---

## 1. 지금까지의 결과 (숫자는 모두 실측)

### 1-1. 모델별 결과

| 평가 | 3B 베이스라인 | v1 (Spider 학습) | v2 (+한국어 다중 JOIN) | v3 (+JOIN 균형) | 7B 베이스라인 |
|---|---|---|---|---|---|
| Spider dev 1,034문제 (영어) | 61.1% | 73.4%‡ | 71.9% | 72.1% | 측정 안 함 |
| 직접 만든 한국어 쇼핑몰 100문제 | 70% | 67% | 67% | 67% | **79%** |
| └ JOIN 2개 이상 (14문제) | **8** | 2 | 5 | 4 | 7 |
| 외부 LLM 4곳이 만든 한국어 118문항 | 73.7% | 61.0% | 61.0% | 69.5% | **86.4%** |
| └ JOIN 0개 (59) | 90% | 86% | 81% | 90% | **93%** |
| └ JOIN 1개 (18) | **94%** | 78% | 72% | 78% | 83% |
| └ JOIN 2개 이상 (41) | 41% | 17% | 27% | 37% | **78%** |
| └ SQL 오류율 | 8.5% | 21.2% | 25.4% | 14.4% | **0.8%** |
| 평균 응답 (CPU, 외부 질문) | 6.8초 | 6.9초 | 7.5초 | 7.7초 | 13.6초 |

- **‡ v1의 Spider만 처음 컴퓨터 값**입니다. 나머지는 모두 이 컴퓨터(Ollama 0.34.2 → 오후부터 0.35.1)에서 잰 값입니다. **v1 Spider를 다음 컴퓨터에서 재는 것이 4-1의 첫 작업**입니다.
- 환경이 바뀌면 같은 모델도 숫자가 조금 달라집니다: Spider 베이스라인 61.8 → 61.1, v2 73.1 → 71.9, 예시 행 65.7 → 65.3 (처음 컴퓨터 → 이 컴퓨터). **1%p 안팎의 차이는 실력 차이로 보지 않습니다.**
- 7B는 3B 베이스라인 대비 외부 질문 새로 맞음 18 / 새로 틀림 3 (z ≈ 3.3), 100문제 12 / 3 (z ≈ 2.3)으로 확실한 차이입니다.

### 1-2. 학습 없는 방법

| 방법 | Spider | 직접 만든 100문제 | 외부 118문항 |
|---|---|---|---|
| 3B 베이스라인 (기준) | 61.1% | 70% | 73.7% |
| + 예시 행 3개 | **65.3%** (새로 맞음 70 / 새로 틀림 27) | 68% (1 / 3) | 74.6% (6 / 5) |
| 3개 다수결 (베이스라인, v3, 예시 행) | 69.8% | 76% | 76.3% |
| 5개 다수결 (위 3개 + v2, v1) | **v1 측정 후 (4-2)** | 78% | 80.5% |
| 자동수정 (처음 컴퓨터) | v1 73.4 → 74.4% | | |

- **예시 행**: Spider에는 효과(+4.2%p), 한국어에는 효과 없음. 쇼핑몰 스키마에는 이미 값 설명 주석(`-- '일반', '실버', ...`)이 있어서 새 정보가 적은 것으로 봄. README에 기록함.
- **다수결 조합은 Spider 측정 전에 미리 고정**했습니다 (시험지에 맞춰 조합을 고르지 않기 위해). 후보 순서 = 동률일 때 우선순위: 베이스라인 → v3 → 예시 행 → v2 → v1.

### 1-3. Spider에서 다수결이 손해인 이유 (중요)

| 표 수 (같은 결과를 낸 후보 수) | 문제 수 | 다수결 정답 | v3 혼자 정답 |
|---|---|---|---|
| 3표 (셋 다 같음) | 641 | 566 | 566 |
| 2표 | 229 | 99 | **115** |
| 1표 (셋 다 다름) | 128 | 57 | **65** |
| 0표 (셋 다 실행 오류) | 36 | 0 | 0 |

- **베이스라인과 "베이스라인 + 예시 행"은 같은 모델이라 답이 비슷합니다.** 그래서 2표 상황에서 둘이 한 편이 되어, Spider에서 더 강한 v3의 답을 이겨 버립니다. 한국어에서는 베이스라인이 가장 강해서 이 문제가 드러나지 않았습니다.
- 순서를 바꿔 v3를 맨 앞에 둬도 70.8%로 v3 혼자(72.1%)보다 낮습니다 (사후 확인용, 결론에 쓰지 않음. 태그 `vote3-v3first`).
- 셋 중 하나라도 맞힌 문제는 821개(79.4%)라서, **"어느 답을 고를지"만 잘 정하면 오를 여지는 큽니다.**
- **교훈**: 다수결은 투표자들이 서로 다른 실수를 할 때만 효과가 있습니다. 같은 모델의 변형을 여러 개 넣으면 오히려 손해일 수 있습니다.
- 5개 다수결(4-2)은 v1·v2·v3 같은 파인튜닝 모델이 3표를 차지하므로 결과가 달라질 수 있습니다. **예측하지 말고 재서 기록**하세요.

### 1-4. v3 판정 (참고)

- 외부 JOIN 2개 이상 v2 이상 유지 ✅ (27 → 37%), JOIN 0·1개 v1 수준 회복 ✅ (90%, 78%), Spider 유지 ✅ (v2 71.9 → v3 72.1, 새로 맞음 54 / 새로 틀림 51)
- v2 → v3 외부 질문: 새로 맞음 19 / 새로 틀림 9 (z ≈ 1.9). 베이스라인 → v3: 7 / 12 (z ≈ -1.1)
- 학습 여부 확인 (`scripts/check_learned.py`, 30문제): v3 30 / v2 27 (Kaggle 1차 실패본은 22 / 26)

### 1-5. 지금 쓸 모델을 고른다면

| 상황 | 추천 |
|---|---|
| 한국어 실무 DB (표 여러 개) | **7B 베이스라인** (가장 정확, 응답 10~14초) |
| 3B만 쓸 수 있고 한국어 | 3B 베이스라인, 응답 시간을 감수할 수 있으면 5개 다수결 |
| 영어·단순 DB | v1 또는 v3 (+ 자동수정) |
| v2 | v3로 대체됨 |

---

## 2. 작업 현황

| # | 작업 | 상태 | 결과물 |
|---|---|---|---|
| 1~3 | 화면에 외부 질문 결과, README 접기, Docker 건강 검진 | ✅ | |
| 4 | v3 데이터·학습·평가·반영 | ✅ | README v3 항목, 화면 v3 버튼·열, `docs/loss_compare.png`, `structure_explanation.md` 6장 |
| 5 | 오류 수정 대화 학습 | 🟡 준비만 됨, 후순위 | `scripts/gen_fix_dialogs.py` |
| 6 | 예시 행 3개 (Spider, 한국어) | ✅ | README 예시 행 항목 |
| 7 | **7B 모델** | 🟡 한국어만 측정 | `ko-base-7b`, `ext-base-7b`. **README·화면 미반영** |
| 11 | **실행 결과 다수결** | 🟡 코드·테스트 완료, 한국어·Spider 3개 측정 | `src/text2sql/vote.py`, `scripts/vote.py`, `tests/test_vote.py`. **Spider 5개 미측정, README·화면 미반영** |
| 8 | Hugging Face 공개 | 🟡 모델 카드 초안만 | `docs/huggingface_model_card.md` |
| 9 | GitHub About, Topics, Pin | ❓ | 사용자가 GitHub 웹에서 직접 |
| 10 | 용량 정리 | ⬜ | 맨 마지막 |

---

## 3. v3 학습 경과 (Kaggle) — README에 기록 완료

Colab 무료 사용량이 바닥나서 **Kaggle Notebooks**(주 약 30시간 GPU, T4)로 옮겼습니다.

| 시도 | Kaggle 버전 | 결과 |
|---|---|---|
| 1차 | Version 1 (2시간 20분) | ❌ step 80부터 끝까지 Loss가 nan. 모델 파일은 정상처럼 보였지만 학습되지 않음 (v3 22 / v2 26) |
| 시험 | Version 2 (20분, `TEST_STEPS = 150`) | ✅ nan 없음 |
| 2차 | Version 3 (약 2시간 35분) | ✅ 1,323단계, nan 0개. Loss 0.381 → 0.056 |

- 원인: 새 Unsloth(2026.9.14)가 자동으로 켠 **padding-free**로 추정. `finetune_kaggle.py`에서 끔 (step당 5.5초 → 6.7초)
- 환경: unsloth 2026.9.14, transformers 5.5.0, trl 0.24.0, torch 2.11.0+cu128, Python 3.13, Tesla T4 1장

---

## 4. 다음 할 일 (순서대로)

### 4-1. Spider v1 측정 (AI, 약 1시간 35분)

6장의 준비가 끝난 뒤:

```bash
# 0) 새 컴퓨터가 이 컴퓨터와 같은 답을 내는지 먼저 확인 (약 5분)
python scripts/predict.py --data data/korean/dev_ko.jsonl --model text2sql-ft-v3 --tag chk-v3 --limit 30
#    outputs/preds_chk-v3.jsonl과 outputs/preds_ko-ft-v3.jsonl 앞 30줄의 pred를 비교 → 거의 같으면(28/30 이상) 진행
#    많이 다르면 v1만 새로 재서 섞지 말고, 사용자와 상의 (4장 끝 "환경이 많이 다를 때")
#    확인이 끝나면 outputs/preds_chk-v3.jsonl은 지운다

# 1) v1 Spider
python scripts/predict.py --model text2sql-ft --tag ft-3b
python scripts/evaluate.py outputs/preds_ft-3b.jsonl
```

참고: 오늘 Ollama 0.34.2 → 0.35.1 자동 업데이트 후 같은 확인에서 60개 중 59개가 같았습니다.

### 4-2. Spider 5개 다수결 (AI, 약 5분)

**후보와 순서는 고정입니다. 바꾸지 마세요** (한국어 vote5와 같은 순서):

```bash
python scripts/vote.py --tag vote5 outputs/preds_base-3b.jsonl outputs/preds_ft-v3.jsonl outputs/preds_base-3b-rows.jsonl outputs/preds_ft-v2.jsonl outputs/preds_ft-3b.jsonl
python scripts/evaluate.py outputs/preds_vote5.jsonl
python scripts/compare.py outputs/preds_ft-v3_eval.jsonl outputs/preds_vote5_eval.jsonl
```

결과가 좋든 나쁘든 그대로 기록합니다. 1-3처럼 "표 수별 정답" 표를 함께 만들면 해석에 도움이 됩니다.

### 4-3. README·화면·문서 반영 (AI, 약 2시간)

- **README**
  - 맨 위 요약표와 "결과 한눈에"에 7B와 다수결 추가. Spider 베이스라인·예시 행도 이 컴퓨터 값(61.1%, 65.3%)으로 바꾸고, 재측정 메모의 "Spider는 베이스라인·v1이 처음 측정값" 문장을 실제 상태에 맞게 고침
  - 새 접기 항목 2개: "7B 베이스라인", "실행 결과 다수결" (한국어 효과, Spider 손해와 그 이유 1-3, 조합을 미리 고정한 방법)
  - 결론을 새로 씀. 예: "3B를 잘 가르쳐도 모델 크기 차이(외부 질문 +12.7%p)를 넘지 못했다. 3B 안에서는 서로 다른 모델의 다수결이 한국어에 효과가 있었지만, 같은 모델의 변형을 섞으면 손해였다" (4-2 결과에 맞게 고칠 것)
  - 로드맵에 7B, 다수결 항목 추가
- **화면**: `web/src/data/report.ts`에 7B·다수결 숫자, `ZReport.tsx`에 구역 추가 (DESIGN.md 따름). 계산대에 "다수결" 모드를 넣을지는 사용자에게 물어볼 것 (선택)
- **structure_explanation.md**: 6장에 "6-8 학습 없이 정확도 올리기 (7B, 다수결)" 추가, 결과 요약표 갱신
- 확인: `cd web && npx tsc --noEmit -p . && npm run build`, `pytest`

### 4-4. 마무리 (사용자 + AI)

| 작업 | 담당 | 내용 |
|---|---|---|
| Hugging Face 공개 | 사용자 로그인 → AI | `huggingface-cli login`은 사용자가 직접. 올릴 모델은 v3 (한국어·영어 균형). 모델 카드에 "한국어 실무는 7B 베이스라인이 더 정확"을 정직하게 적기 |
| GitHub About, Topics, Pin | 사용자 | GitHub 웹에서 |
| v3 LoRA 보관 | 사용자 | `lora_adapter/`(약 130MB)를 Google Drive `text2sql/v3/`에 올렸는지 확인 |
| Kaggle 로그 보관 | 사용자 | Version 1·3 로그를 `outputs/kaggle_v3_try1.log`, `kaggle_v3.log`로 저장 |
| Kaggle 정리 | 사용자 | 위 두 가지 확인 후. Dataset `text2sql-train-v3`는 언제 지워도 됨. 추가 학습을 할 거라면 노트북은 남겨 두기 |
| 데모 GIF 재녹화 | 선택 | 앱을 띄운 상태에서 `web/`의 `npm run record` (v3 버튼이 보이게) |
| 용량 정리 | 맨 마지막 | `scripts/cleanup.ps1` (기본은 미리보기, `-Apply`로 실제 삭제) |

### 4-5. 확장 후보 (선택, 마무리 후)

| 방향 | 내용 | 비용 |
|---|---|---|
| **새 평가 질문 받기 (추천)** | 외부 LLM에게 처음 보는 질문 30~50개를 더 받아 7B·다수결·v3를 재확인. 지금은 같은 218문제로 방법을 고르고 있어서 신뢰도가 가장 크게 오름 | 반나절 |
| 다수결 개선 | 같은 모델의 변형을 빼고 서로 다른 모델만 투표, 또는 3B 다수결에 7B를 넣기 | 짧음 (예측 파일 재사용) |
| 7B Spider 측정 | 약 3시간. 7B의 영어 실력 확인 | 3시간 |
| 7B 파인튜닝 | v3 데이터로 7B 학습. v1처럼 오히려 한국어가 떨어질 수 있으니 별도 단계로 | 하루 이상 |
| 표 연결 경로 힌트 | 프롬프트에 `orders → order_items → products` 같은 경로를 명시하거나 2단계 질문 | 반나절 |
| 오류 수정 대화 학습 | `gen_fix_dialogs.py`. 자동수정 효과가 작아 후순위 | 약 5시간 |

**환경이 많이 다를 때** (4-1의 0번 확인에서 같은 답이 28/30 미만): v1만 새로 재서 이 컴퓨터 결과와 섞으면 비교가 흐려집니다. 선택지는 (a) 다수결에 쓰는 5개 모델의 Spider를 새 컴퓨터에서 모두 다시 재기 (약 7시간), (b) 다르다는 사실을 README에 적고 섞어서 쓰기. 사용자에게 고르게 하세요.

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
| 결과 | Version → Output 탭. `vN/` 폴더만 받으면 됨 (`huggingface_tokenizers_cache`, `unsloth_compiled_cache`는 임시 파일) |
| 학습 확인 | 받은 GGUF를 등록한 뒤 `scripts/check_learned.py`로 새 데이터 문제를 맞히는지 확인 |

Colab용 `train/finetune_unsloth.py`에는 nan 대응이 들어가 있지 않습니다. 다시 Colab을 쓴다면 같은 수정(`padding_free=False`, Monitor)을 옮겨야 해요.

---

## 6. 새 컴퓨터에서 준비할 것

### 6-1. 체크리스트

| # | 준비물 | 크기 | 방법 | 확인 |
|---|---|---|---|---|
| 1 | **`outputs/` 폴더** | 약 8MB | **이 컴퓨터에서 폴더째 복사 (필수).** Git에 없고, 다시 만들려면 예측을 전부 다시 돌려야 함 (10시간 이상) | 6-3의 태그가 모두 있는지 |
| 2 | 저장소 | | `git clone https://github.com/dyj02056/local_LLM_build.git` (또는 `git pull`) | 마지막 커밋이 이 문서가 들어간 커밋인지 |
| 3 | Python 3.10 이상 + 가상환경 | | 6-2 | `pytest` 39개 통과 |
| 4 | Ollama | | 설치 후 **자동 업데이트를 끄기** (오늘 측정 중 자동 업데이트로 Ollama가 꺼져 측정이 실패함). 이 컴퓨터는 0.35.1 | `ollama --version` |
| 5 | GGUF 3개 | 각 1.9GB | `models/*.gguf`(v1), `models/v2/`, `models/v3/`에 같은 이름으로. 이 컴퓨터에서 복사하거나 Drive `text2sql/gguf_out/`, `text2sql/v2/gguf_out/`, Kaggle `v3_training` Version 3 Output | `ollama list`에 `text2sql-ft`, `-v2`, `-v3` |
| 6 | 베이스라인 모델 | 1.9GB, 4.7GB | `ollama pull qwen2.5-coder:3b`, `ollama pull qwen2.5-coder:7b` (7B는 4-5를 할 때만 필요) | `ollama list` |
| 7 | Spider 데이터 | 1.7GB | https://yale-lily.github.io/spider 의 `spider_data.zip`을 `data/spider/`에 풀기 | `data/spider/database/`, `dev.json` |
| 8 | 생성 데이터 | 작음~50MB | 6-2의 스크립트 (고정 seed라 똑같이 만들어짐) | `data/sft/dev.jsonl`, `data/sft_rows/dev.jsonl` |
| 9 | Node.js | | 화면 빌드용 | `npm run build` |
| 10 | 절전 끄기 | | Spider 측정이 1시간 30분 걸리므로 그동안 절전 모드로 들어가지 않게 | |

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

- 이 컴퓨터에서는 `python` 명령이 없고 `.venv\Scripts\python.exe`로 실행했습니다. 새 컴퓨터도 가상환경을 켠 뒤 실행하세요.
- 한글이 깨지면 `PYTHONIOENCODING=utf-8` (Git Bash: `export PYTHONIOENCODING=utf-8`)

### 6-3. `outputs/` 태그 (`preds_<태그>_eval.jsonl`이 채점 결과)

| 태그 | 내용 | 측정 컴퓨터 |
|---|---|---|
| `base-3b`, `base-3b-rows` | Spider, 3B 베이스라인 / + 예시 행 | 이 컴퓨터 (0.35.1) |
| `ft-v2`, `ft-v3` | Spider, v2 / v3 | 이 컴퓨터 (0.34.2) |
| `ft-3b` | Spider, v1 | **없음 → 4-1에서 측정** |
| `vote3`, `vote3-v3first` | Spider 3개 다수결 (정식 / 사후 확인용) | 위 파일로 계산 |
| `ko-base-3b`, `ko-ft-3b`, `ko-ft-v2`, `ko-ft-v3` | 직접 만든 한국어 100문제 | 이 컴퓨터 (0.34.2) |
| `ext-base-3b`, `ext-ft-3b`, `ext-ft-v2`, `ext-ft-v3` | 외부 LLM 118문항 (`--tie-aware`) | 이 컴퓨터 (0.34.2) |
| `ko-base-3b-rows`, `ext-base-3b-rows` | 한국어, 3B 베이스라인 + 예시 행 | 이 컴퓨터 (0.34.2) |
| `ko-base-7b`, `ext-base-7b` | 한국어, 7B 베이스라인 | 이 컴퓨터 (0.35.1) |
| `ko-vote3`, `ko-vote5`, `ext-vote3`, `ext-vote5` | 한국어 다수결 | 위 파일로 계산 |
| `report_external.md` | `report_external.py` 출력 | |

처음 컴퓨터에만 있는 것: 자동수정 실험(`*-sc*`), 처음 측정한 Spider `base-3b`·`ft-3b`·`base-3b-rows`. README의 자동수정 숫자와 v1 Spider 73.4%는 그 결과입니다.

---

## 7. 알아 둘 점 (작업하며 겪은 함정)

| 상황 | 내용 |
|---|---|
| **Ollama 자동 업데이트** | 측정 중 Ollama가 업데이트되며 꺼져 예측이 모두 연결 오류로 실패했습니다. 긴 측정 전에는 자동 업데이트를 끄고, 측정 스크립트에 재시도를 넣으세요. `predict.py`는 이어서 실행되므로 다시 돌리면 됩니다 (빈 결과 파일은 지우고) |
| **환경 차이** | 같은 모델·같은 질문도 컴퓨터나 Ollama 버전이 다르면 1~3%가 다른 답을 냅니다. 비교는 같은 환경에서 잰 값끼리 하고, 섞을 때는 README에 표시하세요 |
| **다수결 후보** | 같은 모델의 변형(베이스라인과 베이스라인 + 예시 행)을 함께 넣으면 한 편이 되어 강한 모델을 이깁니다 (1-3). 후보 조합과 순서는 결과를 보기 전에 정하세요 |
| **시험지 재사용** | 같은 218문제로 방법을 계속 고르면 그 시험지에만 맞는 방법을 고를 위험이 있습니다. 새 결론은 다른 평가셋(Spider)에서도 확인하세요 |
| **Kaggle nan** | 새 Unsloth의 padding-free 자동 활성화로 step 80부터 nan이 났습니다. `finetune_kaggle.py`에서 끔 |
| **학습 확인** | GGUF가 답을 낸다고 학습된 게 아닙니다. loss 기록(nan 여부)과 `check_learned.py`로 확인하세요 |
| 평가 공정성 | 학습 데이터에 평가용 `shop` DB나 쇼핑몰 형태 DB를 쓰지 않습니다. 평가 질문과 겹치는 질문은 생성 스크립트가 자동으로 뺍니다 |
| 정렬 동점 | 새 질문셋은 `scripts/check_order_ties.py`로 검사하고, 동점이 있으면 `evaluate.py --tie-aware`로 채점 |
| 예시 행 프롬프트 | 파인튜닝 모델에는 학습 때와 같은 프롬프트만 줍니다. 예시 행은 베이스라인에만 적용했습니다 |
| CPU 경쟁 | 평가 중에는 Docker의 Ollama나 화면으로 질문하지 마세요 (응답 시간이 부풀려짐) |
| 평가 이어서 하기 | `predict.py`는 이미 만든 줄을 건너뜁니다. 설정을 바꾸면 `--tag`를 바꾸거나 기존 파일을 지우세요 |
| 한글 출력 | 콘솔 한글이 깨지면 `PYTHONIOENCODING=utf-8`. `.ps1`은 BOM 있는 UTF-8로 저장 |
| Loss 비교 | 템플릿 데이터를 섞으면 Loss가 낮아지지만 실력이 좋아졌다는 뜻은 아닙니다. 판단은 항상 평가 정확도로 합니다 |
| 화면 데이터 | `web/src/data/report.ts`(손으로 관리)와 `scripts/export_demo_data.py`(자동). 결과가 바뀌면 둘 다 갱신하고 `npm run build` |
| 브라우저 미리보기 | 앱 창이 가려지면 `requestAnimationFrame`이 멈춥니다. 시간 지연에는 `setTimeout`을 씁니다 |

---

## 8. 작업 방식 (이 프로젝트 사용자와 일할 때)

- 사용자는 **비전공자 관점의 쉬운 설명**을 선호합니다. 명령어와 클릭 순서는 단계별로, 결과 해석은 **표와 비유**로 설명합니다.
- 오래 걸리는 작업은 **예상 종료 시각(몇 시 몇 분)** 을 알려 주고, 바뀌면 다시 알려 줍니다. 중간 측정이 끝나도 AI에게 자동 알림이 오지 않으니, 사용자가 진행 상황을 물으면 그때 확인합니다.
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
| 학습 데이터 생성 | `scripts/gen_korean_train_v3.py`(v3), `gen_korean_train.py`(v2), `gen_fix_dialogs.py`(오류 수정 대화), `make_train_v2.py`(Spider와 합치기) |
| 평가 데이터 생성 | `scripts/prepare_spider.py`, `prepare_korean.py`, `prepare_external.py` (셋 다 `--sample-rows`로 예시 행 포함 가능) |
| 평가·비교 도구 | `scripts/predict.py`, `evaluate.py`, `compare.py`, `report_external.py`, `self_correct.py`, `check_learned.py`(학습 여부 확인), `vote.py`(다수결) |
| 다수결 로직 | `src/text2sql/vote.py`, 테스트 `tests/test_vote.py` |
| Loss 기록 | `loss_table/loss_table.txt`(v1), `loss_table_v2.txt`, `loss_table_v3.txt`(2차 성공본, nan 0개) |
| 한국어 평가 질문 | `data/korean/questions.json` (직접 100개), `questions_external.json` (외부 118개) |
| 모델 카드 초안 | `docs/huggingface_model_card.md` |
| 화면 코드 | `web/src/` (`components/Receipt.tsx`, `ZReport.tsx`, `data/report.ts`) |
| 서버 | `app/main.py` (`base`, `ft`, `ft2`, `ft3` 모델 키) |
| 디자인 규칙 | `DESIGN.md`, `PRODUCT.md`, `.impeccable/` |
