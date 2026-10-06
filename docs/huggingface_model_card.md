---
# Hugging Face 모델 저장소의 README.md로 올리는 초안입니다.
# <계정>, <저장소> 를 바꾸고, 올릴 모델(v1/v2/v3)에 맞게 "이 모델" 줄을 고친 뒤 이 주석 세 줄을 지우세요.
language:
  - ko
  - en
license: other
license_name: qwen-research
license_link: https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct/blob/main/LICENSE
base_model: Qwen/Qwen2.5-Coder-3B-Instruct
datasets:
  - xlangai/spider
pipeline_tag: text-generation
tags:
  - text-to-sql
  - sql
  - sqlite
  - qlora
  - gguf
  - ollama
  - korean
---

# Qwen2.5-Coder-3B Text-to-SQL (QLoRA, GGUF)

자연어 질문과 SQLite 스키마를 받아 **SELECT 문 한 줄**을 쓰는 3B 모델입니다.
[Qwen2.5-Coder-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct)를 Spider로 QLoRA 파인튜닝하고 q4_k_m GGUF(1.9GB)로 변환해, **GPU 없이 CPU에서** Ollama로 돌릴 수 있습니다.

- 이 모델: **v1** (Spider train 8,659문제로 학습)
- 코드, 평가 스크립트, 데모 화면: https://github.com/dyj02056/local_LLM_build

## 바로 쓰기 (Ollama)

```bash
ollama run hf.co/<계정>/<저장소>
```

학습 때와 같은 프롬프트를 써야 성능이 나옵니다. 시스템 프롬프트와 사용자 메시지는 아래 형식을 그대로 쓰세요.

```text
[system]
You are an expert SQLite assistant. Given a database schema and a question, write a single SQLite SELECT query that answers the question. Output only the SQL query, without explanation.

[user]
### Schema
CREATE TABLE ... (DB의 CREATE TABLE 문 전체)

### Question
도시별 회원 수를 많은 순으로 보여 줘.
```

저장소의 `Modelfile`을 받아 `ollama create text2sql-ft -f Modelfile`로 등록해도 됩니다. 시스템 프롬프트가 미리 들어 있습니다.

## 결과

실행 정확도(Execution Accuracy)입니다. 생성한 SQL을 실제로 실행해 정답 SQL과 결과 행이 같으면 정답으로 봅니다.

| 평가 | 베이스라인 (zero-shot) | **v1 (이 모델)** | v2 (+한국어 다중 JOIN) |
|---|---|---|---|
| Spider dev 1,034문제 (영어) | 61.8% | **73.4%** | 73.1% |
| 직접 만든 한국어 쇼핑몰 100문제 | 71% | 66% | 68% |
| 외부 LLM 4곳이 쓴 한국어 118문항 | 73.7% | 61.0% | 61.9% |
| └ 정답에 JOIN 2개 이상 (41문항) | 46% | 17% | 34% |

- Spider에서 SQL 오류율은 13.4% → 6.1%로 줄었고, 평균 응답 시간은 CPU에서 5.04초입니다.
- 실행 오류 메시지를 다시 보여 주고 고치게 하는 self-correction을 더하면 Spider 74.4%입니다.

## 한계 (꼭 읽어 주세요)

- **한국어, 다중 JOIN에 약합니다.** Spider 점수는 올랐지만, 테이블 3개 이상을 이어야 하는 한국어 질문에서는 베이스라인보다 크게 낮습니다. 중간 테이블(예: `order_items`)을 건너뛰는 버릇이 있습니다.
- v2는 이 약점을 일부 고쳤지만, 반대로 필요 없는 JOIN을 붙이는 실수가 생겼습니다.
- 실제 서비스 DB에 쓸 때는 **읽기 전용 연결**과 실행 시간 제한을 꼭 거세요. 모델이 SELECT만 쓰도록 학습됐지만 보장되지는 않습니다.
- 한국어 평가셋은 100문제와 118문항 규모라 통계적 한계가 있습니다.

## 학습

| 항목 | 값 |
|---|---|
| 데이터 | Spider train 8,659문제 (`train_spider.json` + `train_others.json`), 1 epoch |
| 방식 | 4bit QLoRA, r=16, alpha=16, lr 2e-4 (cosine), 배치 2 × 누적 4, Colab T4, Unsloth |
| Loss | SQL(assistant 응답) 부분에만 계산. 0.404 → 0.080 |
| 변환 | q4_k_m GGUF |

## 라이선스

- 모델 가중치는 베이스 모델의 라이선스를 따릅니다: [Qwen2.5-Coder-3B-Instruct LICENSE](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct/blob/main/LICENSE). 올리기 전에 링크에서 조건(상업적 이용 등)을 꼭 확인하세요.
- 학습 데이터 [Spider](https://yale-lily.github.io/spider)는 CC BY-SA 4.0입니다.

```bibtex
@inproceedings{yu2018spider,
  title     = {Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task},
  author    = {Yu, Tao and Zhang, Rui and Yang, Kai and Yasunaga, Michihiro and Wang, Dongxu and Li, Zifan and Ma, James and Li, Irene and Yao, Qingning and Roman, Shanelle and Zhang, Zilin and Radev, Dragomir},
  booktitle = {EMNLP},
  year      = {2018}
}
```
