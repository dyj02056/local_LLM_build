# Google Colab(T4 GPU)용 QLoRA 파인튜닝 스크립트.
# 셀 단위(# %%)로 나눠 두었으니 Colab에 셀별로 복사해 실행하세요.
# 준비물: 로컬에서 만든 data/sft/train.jsonl 을 Colab의 같은 경로(/content/data/sft/)에 업로드.
# Colab 파일은 런타임이 끊기면 사라지므로 결과물은 단계마다 Google Drive로 복사한다.
# Unsloth/TRL 버전에 따라 인자명이 바뀔 수 있으니 오류가 나면 Unsloth 공식 노트북을 참고하세요.

# %% 0. GPU 확인 (Tesla T4가 보여야 함)
# !nvidia-smi

# %% 1. 설치
# !pip install unsloth

# %% 2. Google Drive 연결 (결과물 백업용)
from google.colab import drive

drive.mount("/content/drive")
BACKUP_DIR = "/content/drive/MyDrive/text2sql"

# %% 3. 모델 로드 (4bit)
from unsloth import FastLanguageModel

MODEL_NAME = "unsloth/Qwen2.5-Coder-3B-Instruct"  # 7B로 바꾸면 성능↑, 로컬 추론 속도↓
MAX_SEQ_LEN = 2048

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LEN,
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=16,
    lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

# %% 4. 데이터 (prompt.py와 동일한 chat 형식)
from datasets import load_dataset

ds = load_dataset("json", data_files="data/sft/train.jsonl", split="train")
ds = ds.map(lambda ex: {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False)})
# 스키마가 너무 길어 잘리는 샘플 제외
ds = ds.filter(lambda ex: len(tokenizer(ex["text"]).input_ids) <= MAX_SEQ_LEN)
print(ds)

# %% 5. 학습 (T4는 bf16 미지원 → fp16)
from trl import SFTConfig, SFTTrainer
from unsloth.chat_templates import train_on_responses_only

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=ds,
    args=SFTConfig(
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=1,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        optim="adamw_8bit",
        fp16=True,
        logging_steps=10,
        output_dir="checkpoints",
        report_to="none",
    ),
)
# 손실은 SQL(assistant 응답) 부분에만 계산 — 스키마를 외우는 데 용량을 쓰지 않도록
trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)
trainer.train()

# %% 6. LoRA 어댑터 저장 + Drive 백업 (GGUF 변환이 실패해도 학습 결과는 보존)
import shutil

model.save_pretrained("lora_adapter")
tokenizer.save_pretrained("lora_adapter")
shutil.copytree("lora_adapter", f"{BACKUP_DIR}/lora_adapter", dirs_exist_ok=True)

# %% 7. Ollama용 GGUF 변환 + Drive 백업
model.save_pretrained_gguf("gguf_out", tokenizer, quantization_method="q4_k_m")
shutil.copytree("gguf_out", f"{BACKUP_DIR}/gguf_out", dirs_exist_ok=True)
# Drive의 text2sql/gguf_out 에서 .gguf 파일을 내려받아 로컬에서:
#   ollama create text2sql-ft -f Modelfile
