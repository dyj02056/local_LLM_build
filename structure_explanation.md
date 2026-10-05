# 프로젝트 한눈에 보기: Local Text-to-SQL

> 한국어로 질문하면, 내 컴퓨터에서 돌아가는 AI가 데이터베이스 질의문(SQL)을 써서 답을 찾아 주는 프로그램입니다.
> 이 문서는 전공 지식이 없어도 프로젝트의 구성과 사용법을 이해할 수 있도록 정리했습니다.

---

## 1. 이 프로젝트는 무엇인가요?

회사의 데이터는 보통 **데이터베이스(DB)** 라는 거대한 엑셀 묶음에 들어 있습니다. 여기서 원하는 정보를 꺼내려면 **SQL**이라는 전용 언어로 물어봐야 해서, SQL을 모르는 사람은 개발자에게 부탁해야 하죠.

이 프로젝트는 그 통역을 AI에게 맡깁니다.

```
"서울에 사는 고객은 몇 명이야?"        ← 사람이 한국어로 질문
        │
        ▼  AI(언어 모델)가 번역
SELECT count(*) FROM customers WHERE city = '서울'   ← SQL
        │
        ▼  데이터베이스에서 실행
59명                                      ← 답
```

**특징 세 가지**

| 특징 | 쉽게 말하면 |
|---|---|
| **로컬 실행** | 인터넷의 유료 AI(ChatGPT 등)가 아니라 **내 컴퓨터 안에서** 돌아갑니다. 회사 데이터가 밖으로 나가지 않아요. |
| **직접 학습시킨 AI** | 공개된 작은 AI 모델을 SQL 문제 8,659개로 **추가 공부(파인튜닝)** 시켜 실력을 높였습니다. |
| **정직한 측정** | 좋아진 점뿐 아니라 **나빠진 점과 실패한 실험도** 숫자로 기록했습니다. |

---

## 2. 사용한 기술 (기술 스택)

### 2-1. 전체 그림

```
[사용자 화면]            [중간 관리자]                [AI 엔진]
 웹 브라우저   ──질문──▶  FastAPI 서버   ──질문──▶   Ollama (AI 모델)
 (React)      ◀─영수증──  (전달, 안전 검사) ◀──SQL───
                              │
                              │ SQL 실행 (읽기 전용)
                              ▼
                         [데이터 창고]
                         SQLite 데이터베이스
```

### 2-2. 기술별 역할

| 분류 | 기술 | 하는 일 | 비유 |
|---|---|---|---|
| **AI 모델** | Qwen2.5-Coder-3B | 질문을 SQL로 바꾸는 두뇌. 코드에 특화된 공개 AI 모델 (30억 개의 숫자로 이루어짐) | 신입 번역가 |
| **AI 학습** | QLoRA, Unsloth | 큰 모델 전체를 다시 가르치지 않고, 작은 "보조 노트"만 붙여 효율적으로 공부시키는 방법 | 교과서는 그대로 두고 요약 노트만 새로 만들기 |
| **학습 장소** | Google Colab (T4 GPU) | 학습에 필요한 고성능 그래픽카드를 무료로 빌려 쓰는 곳 | 학원 자습실 |
| **AI 실행** | Ollama | 학습된 모델을 내 컴퓨터에서 돌려 주는 프로그램 | 번역가가 일하는 사무실 |
| **모델 파일** | GGUF (q4_k_m) | 모델을 약 2GB로 압축한 파일 형식 | 압축 파일(zip) |
| **데이터베이스** | SQLite | 파일 하나로 된 가벼운 DB. 읽기 전용으로 열어 안전하게 사용 | 열람만 가능한 서류함 |
| **서버** | Python, FastAPI | 화면과 AI, DB 사이에서 질문을 전달하고 결과를 돌려주는 중간 관리자 | 접수 창구 직원 |
| **화면** | React, Vite, Tailwind CSS | 웹 브라우저에 보이는 화면을 만드는 도구 | 매장 인테리어 |
| **배포** | Docker, Docker Compose | 프로그램 전체를 상자에 담아 어느 컴퓨터에서든 같은 명령 한 줄로 실행 | 이삿짐 컨테이너 |
| **검증** | pytest | 코드가 의도대로 동작하는지 자동으로 확인하는 테스트 (33개) | 출고 전 품질 검사 |
| **평가 데이터** | Spider | 학계에서 쓰는 공개 SQL 문제집 (영어, 문제 1만여 개) | 공인 모의고사 |

---

## 3. 기능

### 3-1. 데모 화면 "질의 영수증"

질문 하나를 넣으면 **계산대 영수증 한 장**이 인쇄되듯 결과가 나옵니다.

| 영수증 항목 | 의미 |
|---|---|
| 질문 | 입력한 한국어 질문 |
| SQL | AI가 쓴 질의문 (절마다 한 줄씩) |
| 결과 | DB에서 찾은 답 (표 형태) |
| 합계 | SQL 생성 시간 + DB 실행 시간 |
| 빨간 VOID 줄 | 실행에 실패해서 AI가 고쳐 쓴 SQL (자동수정 기능) |

### 3-2. 화면 구성

| 화면 | 할 수 있는 일 |
|---|---|
| **계산대** | DB와 모델을 고르고 질문을 입력해 영수증 인쇄 |
| └ 모델 선택 | **베이스라인**(공부 전 원래 모델) / **파인튜닝 v1**(SQL 문제집으로 공부) / **파인튜닝 v2**(v1 + 한국어 문제 추가 공부) / **모두 비교** |
| └ 자동수정 | SQL에 오류가 나면 오류 메시지를 보여 주고 최대 2번 다시 쓰게 함 (정답은 보여 주지 않음) |
| └ 평가 문제 100개 | 칸을 누르면 미리 준비된 질문이 입력됨. 칸 아래 막대는 각 모델의 실제 채점 결과 (실선 = 정답, 점선 = 오답) |
| **정산 리포트** | 모든 평가 결과를 계산대 "일일 정산표" 형식으로 정리 |

### 3-3. 안전장치

AI가 실수로 "데이터를 지워라" 같은 명령을 써도 실행되지 않습니다.

| 장치 | 내용 |
|---|---|
| 읽기 전용 연결 | DB를 "보기만 가능"한 상태로 엽니다 |
| 명령 허가제 | 조회(SELECT) 외의 모든 명령(삭제, 수정, 설정 변경)을 DB가 거부합니다 |
| 시간 제한 | 5초 넘게 걸리는 질의는 자동으로 멈춥니다 |
| 결과 제한 | 한 번에 최대 200행까지만 보여 줍니다 |

---

## 4. 사용법

### 4-1. 준비물

| 준비물 | 용도 | 비고 |
|---|---|---|
| Docker Desktop | 가장 쉬운 실행 방법 | 방법 A |
| Python 3.10 이상, Node.js | 직접 실행할 때 | 방법 B |
| Ollama + AI 모델 3개 | AI 모델 실행 | 방법 B. 아래 **(1)** 참고 |
| 모델 파일 (`.gguf`) | 파인튜닝된 AI 2개의 원본 파일 | 용량(각 약 2GB) 때문에 GitHub에는 없음. 아래 **(2)** 참고 |

#### (1) Ollama에 AI 모델 설치하기

이 프로젝트는 AI 모델 **3개**를 비교합니다. 셋 다 같은 모델에서 출발했고, 공부를 얼마나 더 시켰는지만 다릅니다.

| Ollama에서 쓰는 이름 | 정체 | 구하는 방법 |
|---|---|---|
| `qwen2.5-coder:3b` | **베이스라인.** 알리바바가 공개한 코드 전용 AI 모델 **Qwen2.5-Coder-3B-Instruct** 원본 (30억 개의 숫자로 된 작은 모델) | Ollama 공식 저장소에서 **명령 한 줄로 내려받기** |
| `text2sql-ft` | **파인튜닝 v1.** 위 모델에 SQL 문제집(Spider) 8,659문제를 추가로 공부시킨 것 | 공식 저장소에 없음 → **GGUF 파일로 직접 등록** |
| `text2sql-ft-v2` | **파인튜닝 v2.** v1 공부에 한국어 다중 연결 문제 940개를 더한 것 | 공식 저장소에 없음 → **GGUF 파일로 직접 등록** |

Ollama가 설치되어 있다는 가정하에, 명령 프롬프트(cmd)나 PowerShell을 열고 차례로 입력합니다.

**① 베이스라인 모델 내려받기 (약 2GB, 인터넷 속도에 따라 몇 분)**

```bash
ollama pull qwen2.5-coder:3b
```

앱스토어에서 앱을 받는 것과 같습니다. `pull`은 "공식 저장소에서 가져와라"라는 뜻이에요. 마지막에 `success`가 나오면 끝입니다.

**② 파인튜닝 모델 2개 등록하기 (각 1분 정도)**

GGUF 파일을 `models/`와 `models/v2/`에 넣은 뒤(아래 (2) 참고), **프로젝트 폴더에서** 실행합니다.

```bash
ollama create text2sql-ft -f models/Modelfile
ollama create text2sql-ft-v2 -f models/v2/Modelfile
```

`create`는 "이 설명서(Modelfile)를 보고 모델을 등록해라"라는 뜻입니다. Modelfile에는 "같은 폴더의 GGUF 파일을 쓰고, 이런 말투로 대화하라"는 내용이 들어 있어요. 인터넷 없이 내 컴퓨터 안에서만 처리됩니다.

**③ 잘 설치됐는지 확인하기**

```bash
ollama list
```

목록에 `qwen2.5-coder:3b`, `text2sql-ft`, `text2sql-ft-v2` 세 줄이 보이고, 크기가 각각 **약 1.9GB**면 성공입니다.

실제로 잘 동작하는지는 프로그램을 실행한 뒤 **화면 오른쪽 위**에서 확인하는 게 가장 쉽습니다. `Ollama 연결됨 · 모델 3/3`이 보이면 세 모델 모두 준비된 거예요.

> **v2 파일이 없다면?** 베이스라인과 v1만 등록해도 프로그램은 돌아갑니다. 화면에서 "파인튜닝 v2" 버튼만 비활성화돼요.

#### (2) 모델 파일(`.gguf`) 준비하기

**GGUF**는 학습을 마친 AI를 **약 2GB로 압축해 한 파일로 묶은 것**입니다 (비유하면 완성된 요리를 밀키트로 포장한 것). 상황에 따라 아래 세 가지 방법 중 하나를 고르세요. 위에 있을수록 쉽고 빠릅니다.

| 방법 | 언제 쓰나 | 걸리는 시간 |
|---|---|---|
| **A. 파일 복사** | 이미 GGUF가 있는 컴퓨터나 Google Drive가 있을 때 | 몇 분 |
| **B. 보조 노트로 다시 만들기** | GGUF는 없지만 Google Drive에 `lora_adapter` 폴더가 남아 있을 때 | 20~30분 (Colab) |
| **C. 처음부터 다시 학습** | 아무것도 남아 있지 않을 때 | 약 3시간 (Colab) |

---

**방법 A. 파일 복사 (가장 쉬움)**

GGUF는 그냥 파일이라서 USB, 외장 하드, 클라우드로 옮기면 됩니다.

1. 원래 컴퓨터의 `models/Qwen2.5-Coder-3B-Instruct.Q4_K_M.gguf`(v1)와 `models/v2/Qwen2.5-Coder-3B-Instruct.Q4_K_M.gguf`(v2)를 복사합니다.
   - 또는 Google Drive에서 받습니다: v1은 `내 드라이브/text2sql/gguf_out/`, v2는 `내 드라이브/text2sql/v2/gguf_out/`
2. 새 컴퓨터의 프로젝트 폴더에서 **같은 위치**(`models/`, `models/v2/`)에 넣습니다.
3. 위 (1)의 ②번 명령으로 등록합니다.

> 두 파일의 이름이 같으니 **폴더를 헷갈리지 않게** 주의하세요. v1은 `models/` 바로 아래, v2는 `models/v2/` 아래입니다.

---

**방법 B. 보조 노트(LoRA)로 GGUF만 다시 만들기**

파인튜닝은 원본 모델은 그대로 두고 **작은 보조 노트(LoRA, 수십 MB)** 만 새로 만드는 방식입니다. 이 노트가 Google Drive에 남아 있으면, 원본 모델에 노트를 붙여서 GGUF로 포장하는 작업만 다시 하면 돼요. **학습을 다시 하지 않아도 됩니다.**

| 버전 | 보조 노트 위치 (Google Drive) |
|---|---|
| v1 | `내 드라이브/text2sql/lora_adapter/` |
| v2 | `내 드라이브/text2sql/v2/lora_adapter/` |

1. [Google Colab](https://colab.research.google.com)에서 새 노트북을 열고, 상단 메뉴 **런타임 → 런타임 유형 변경 → T4 GPU**를 선택합니다.
2. 아래 셀들을 차례로 붙여 넣고 실행합니다. 맨 위의 `RUN`만 원하는 버전(`"v1"` 또는 `"v2"`)으로 바꾸세요.

```python
# 셀 1. 설치 (2~4분)
!pip install unsloth
```

```python
# 셀 2. Google Drive 연결 (허용 창이 뜨면 허용)
from google.colab import drive
drive.mount("/content/drive")

RUN = "v2"   # v1을 만들려면 "v1"
ADAPTER = {"v1": "/content/drive/MyDrive/text2sql/lora_adapter",
           "v2": "/content/drive/MyDrive/text2sql/v2/lora_adapter"}[RUN]
OUT_DIR = {"v1": "/content/drive/MyDrive/text2sql/gguf_out",
           "v2": "/content/drive/MyDrive/text2sql/v2/gguf_out"}[RUN]
```

```python
# 셀 3. 원본 모델 + 보조 노트 불러오기 (1~3분)
# 보조 노트 폴더 안에 "원본 모델이 무엇인지"가 적혀 있어서, 원본도 자동으로 함께 내려받는다
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=ADAPTER,
    max_seq_length=2048,
    load_in_4bit=True,
)
```

```python
# 셀 4. GGUF로 포장해서 Drive에 저장 (15~30분)
import glob, os, shutil

model.save_pretrained_gguf("gguf_out", tokenizer, quantization_method="q4_k_m")

os.makedirs(OUT_DIR, exist_ok=True)
for p in glob.glob("gguf_out*/**/*.gguf", recursive=True) + glob.glob("*.gguf"):
    if "q4_k_m" in os.path.basename(p).lower():
        shutil.copy2(p, f"{OUT_DIR}/{os.path.basename(p)}")
        print("저장 완료:", OUT_DIR, os.path.basename(p))
```

3. `저장 완료`가 나오면 Drive의 해당 `gguf_out` 폴더에서 `.gguf` 파일을 받아 방법 A의 2~3번처럼 넣고 등록합니다.

---

**방법 C. 처음부터 다시 학습하기**

보조 노트까지 없을 때만 씁니다. 같은 데이터와 같은 설정으로 학습하므로 **비슷한 모델**이 만들어집니다 (AI 학습에는 무작위 요소가 있어서 숫자가 완전히 똑같지는 않을 수 있어요).

**① 학습 데이터 만들기 (내 컴퓨터, 약 10분)**

```bash
# Spider 문제집 준비: https://yale-lily.github.io/spider 에서 spider_data.zip 을 받아 data/spider/ 에 풉니다
python scripts/prepare_spider.py            # v1용: data/sft/train.jsonl

# v2용 한국어 데이터를 추가로 만들 때
python scripts/build_korean_train_dbs.py
python scripts/gen_korean_train.py
python scripts/make_train_v2.py             # v2용: data/sft/train_v2.jsonl
```

**② Colab에서 학습하기 (약 3시간)**

1. Colab에서 T4 GPU를 켭니다.
2. [`train/finetune_unsloth.py`](train/finetune_unsloth.py)의 셀(`# %%`로 나뉜 부분)을 하나씩 붙여 넣습니다.
3. 셀 2의 `RUN`을 `"v1"` 또는 `"v2"`로 정합니다.
4. 학습 파일(`train.jsonl` 또는 `train_v2.jsonl`)을 Colab의 `/content/data/sft/` 폴더에 올립니다.
5. 셀 0부터 7까지 차례로 실행합니다. 셀 5(학습)가 2~2.5시간으로 가장 오래 걸려요.
6. 끝나면 Drive의 `text2sql/<RUN>/gguf_out/`에 GGUF가 저장됩니다. 방법 A처럼 받아서 넣고 등록합니다.

> **주의:** 학습 중에 Colab 탭을 닫거나 PC가 절전 모드로 들어가면 처음부터 다시 해야 합니다.

---

**자주 생기는 문제**

| 증상 | 원인과 해결 |
|---|---|
| `ollama create`에서 파일을 못 찾는다는 오류 | GGUF 파일 이름이 Modelfile 첫 줄(`FROM ./Qwen2.5-Coder-3B-Instruct.Q4_K_M.gguf`)과 다름. 파일 이름을 그대로 바꾸거나 Modelfile 첫 줄을 실제 파일 이름으로 고치세요 |
| 다운로드한 파일이 `.crdownload`로 끝남 | 아직 내려받는 중. 끝날 때까지 기다리세요 |
| 크기가 2GB보다 훨씬 작음 | 다운로드가 중간에 끊김. 다시 받으세요 (정상 크기는 약 1.9GB) |

### 4-2. 방법 A: Docker로 한 번에 실행 (추천)

1. Docker Desktop을 켭니다.
2. 프로젝트 폴더에서 아래 명령을 실행합니다.
   ```bash
   docker compose up --build
   ```
3. 브라우저에서 **http://localhost:8000** 을 엽니다.

처음 한 번은 AI 모델을 내려받느라 몇 분 걸리고 디스크를 약 13GB 씁니다. 끌 때는 `docker compose down`을 실행합니다.

### 4-3. 방법 B: 직접 실행

```bash
# 1) 파이썬 환경 준비 (처음 한 번)
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

# 2) 한국어 쇼핑몰 DB 만들기 (처음 한 번)
python scripts/build_shop_db.py

# 3) AI 모델 등록 (처음 한 번)
ollama pull qwen2.5-coder:3b
ollama create text2sql-ft -f models/Modelfile
ollama create text2sql-ft-v2 -f models/v2/Modelfile

# 4) 화면 만들기 (처음 한 번)
cd web
npm install
npm run build
cd ..

# 5) 실행
uvicorn app.main:app
```

브라우저에서 **http://localhost:8000** 을 엽니다.

### 4-4. 화면 사용 순서

1. **데이터베이스**: `shop · 가상 쇼핑몰`을 고릅니다 (한국어 질문용).
2. **모델**: 처음에는 `모두 비교`를 추천합니다. 세 모델의 답을 나란히 볼 수 있어요.
3. **질문**: 아래 "평가 문제 100개"에서 칸을 누르거나 직접 입력합니다.
   - 예: `취소된 주문을 빼고 카테고리별 매출을 높은 순으로 보여 줘`
4. **인쇄** 버튼을 누릅니다 (또는 `Ctrl + Enter`).
5. 영수증을 비교합니다. 아래에 "결과 행이 모두 같습니다" 또는 "결과 행이 갈립니다"가 표시됩니다.
6. 상단의 **정산 리포트**에서 전체 평가 결과를 봅니다.

**알아 둘 점**

- 컴퓨터의 CPU로 AI를 돌리므로 질문 하나에 **5~30초** 걸립니다. 첫 질문은 모델을 불러오느라 더 오래 걸려요.
- Spider DB(영어)를 고르면 질문도 **영어로** 해야 합니다.

---

## 5. 폴더 구조

```
local_LLM_build/
├─ app/main.py            접수 창구 (FastAPI 서버, 화면도 함께 제공)
├─ src/text2sql/          핵심 부품
│   ├─ prompt.py            AI에게 주는 질문지 양식
│   ├─ schema.py            DB 구조를 AI가 읽을 수 있게 정리
│   ├─ executor.py          안전한 SQL 실행 (읽기 전용 + 명령 허가제 + 시간 제한)
│   ├─ llm.py               Ollama에 질문 보내기
│   ├─ correct.py           자동수정 (오류를 보고 다시 쓰기)
│   ├─ evaluate.py          채점 (실행 결과가 정답과 같은지)
│   └─ ties.py              정렬 동점 처리 채점
├─ web/                   데모 화면 (React)
├─ scripts/               실험용 도구 모음 (아래 표)
├─ train/finetune_unsloth.py   Colab에서 AI를 학습시키는 코드
├─ models/                모델 설정 파일 (Modelfile). 모델 파일 자체는 직접 넣어야 함
├─ data/korean/           한국어 평가 질문 (직접 만든 100개 + 외부 AI 4곳이 만든 118개)
├─ docs/                  README용 그래프, 스크린샷, 데모 GIF
├─ tests/                 자동 테스트 33개
├─ Dockerfile, docker-compose.yml   Docker 실행 설정
├─ README.md              결과와 분석 (포트폴리오 본문)
├─ PRODUCT.md, DESIGN.md  화면 설계 원칙과 디자인 규칙
└─ structure_explanation.md   이 문서
```

**scripts/ 주요 도구**

| 파일 | 하는 일 |
|---|---|
| `prepare_spider.py` | Spider 문제집을 학습용 형식으로 변환 |
| `predict.py` | AI에게 문제를 풀게 하고 답을 저장 (중단해도 이어서 실행) |
| `evaluate.py` | 답을 채점 (정확도, 오류율, 응답 시간) |
| `compare.py` | 두 모델의 결과를 비교 (유형별, DB별, 좋아진·나빠진 문제) |
| `self_correct.py` | 자동수정 실험 |
| `build_shop_db.py` | 한국어 평가용 가상 쇼핑몰 DB 만들기 |
| `prepare_korean.py` | 한국어 질문의 정답 SQL 검증 (빈 결과, 동점 검사) |
| `build_korean_train_dbs.py`, `gen_korean_train.py`, `make_train_v2.py` | v2 학습용 한국어 데이터 만들기 (도서관·병원·학원·여행사 DB) |
| `prepare_external.py`, `report_external.py` | 외부 AI가 만든 질문으로 평가하고 정리 |
| `plot_loss.py` | 학습 진행 그래프 그리기 |
| `export_demo_data.py` | 화면에 보여 줄 실측 결과 내보내기 |
| `cleanup.ps1` | 프로젝트를 마친 뒤 용량 정리 (기본은 미리보기만) |

---

## 6. 지금까지의 결과 요약

| 실험 | 결과 | 한 줄 해석 |
|---|---|---|
| 파인튜닝 (Spider 영어 1,034문제) | 정확도 **61.8% → 73.4%** | 공부시킨 효과가 확실함 |
| 자동수정 | +1.0%p | 효과가 작음. AI가 오류를 보고도 같은 답을 반복하는 경우가 40~65% |
| 한국어 쇼핑몰 100문제 (직접 제작) | 베이스라인 71%, v1 **66%** | 영어 문제집으로 공부한 AI가 한국어 실무형 문제에서는 오히려 떨어짐. 특히 표를 여러 개 이어야 하는 문제에서 약함 |
| v2 (한국어 다중 연결 문제 940개 추가 학습) | 한국어 68%, 영어 73.1% | 약점이 일부 나아졌지만 베이스라인을 넘지 못함 |
| 외부 AI 4곳(ChatGPT, Gemini, DeepSeek, Meta)이 만든 질문 118개 | 평가 진행 중 | 질문을 같은 사람이 만들어 생긴 편향이 있었는지 확인 |

자세한 숫자와 분석은 [README.md](README.md)에 있습니다.

---

## 7. 용어 사전

| 용어 | 뜻 |
|---|---|
| **LLM (대규모 언어 모델)** | 글을 읽고 쓰는 AI. ChatGPT 같은 것 |
| **SQL** | 데이터베이스에 질문하는 전용 언어 |
| **JOIN** | 여러 표를 연결하는 SQL 동작. 예: 주문 표와 고객 표를 이어서 "누가 샀는지" 확인 |
| **파인튜닝** | 이미 만들어진 AI에게 특정 분야를 추가로 공부시키는 것 |
| **베이스라인** | 비교 기준. 여기서는 공부시키기 전의 원래 모델 |
| **실행 정확도 (EX)** | AI가 쓴 SQL을 실제로 실행했을 때 정답과 같은 결과가 나온 비율 |
| **Loss (손실)** | 학습 중 AI가 틀린 정도. 낮아질수록 학습 데이터를 잘 따라 함 |
| **자동수정 (self-correction)** | 실행 오류가 나면 오류 메시지를 AI에게 보여 주고 다시 쓰게 하는 것 |
| **로컬** | 인터넷 서비스가 아니라 내 컴퓨터에서 실행하는 것 |
| **GPU / CPU** | GPU는 AI 계산에 빠른 그래픽 처리 장치, CPU는 일반 컴퓨터의 처리 장치. 이 프로젝트는 학습은 GPU(Colab), 실행은 CPU(내 PC)로 함 |
| **부호 검정 (z 값)** | 두 모델의 차이가 우연인지 확인하는 간단한 통계. 절댓값이 2 정도를 넘으면 우연으로 보기 어려움 |

---

## 8. 자주 묻는 질문

**Q. 인터넷이 없어도 되나요?**
처음 설치할 때만 필요합니다. 설치가 끝나면 인터넷 없이 내 컴퓨터에서만 동작합니다.

**Q. 답이 왜 이렇게 느린가요?**
AI를 그래픽카드(GPU) 없이 일반 CPU로 돌리기 때문입니다. 대신 별도 장비나 비용이 들지 않아요.

**Q. AI가 데이터를 망가뜨릴 수 있나요?**
아니요. DB를 읽기 전용으로 열고, 조회 외의 모든 명령을 DB 단계에서 거부합니다 (3-3 참고).

**Q. 파인튜닝한 모델이 왜 한국어 문제에서는 더 못하나요?**
영어 문제집으로 공부하면서 "SQL을 짧게 쓰는" 버릇이 생겼고, 표를 여러 개 이어야 하는 문제에서 중간 표를 건너뛰는 실수를 하게 되었습니다. 이 약점을 찾아낸 과정과 고치려는 시도(v2)가 README에 정리되어 있습니다.

**Q. 다 쓰고 나서 용량을 정리하려면?**
`scripts/cleanup.ps1`을 실행하면 지울 목록과 크기를 먼저 보여 줍니다. `-Apply`를 붙여야 실제로 지웁니다 (약 22~26GB).
