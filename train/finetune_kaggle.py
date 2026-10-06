# Kaggle Notebook(T4 GPU)용 QLoRA 파인튜닝 스크립트.
# train/finetune_unsloth.py(Colab용)와 학습 설정은 같고, 저장 위치만 Kaggle에 맞췄다.
#   - Google Drive 대신 /kaggle/working 에 저장 (최대 20GB, 실행이 끝나면 Output 탭에서 내려받음)
#   - 학습 파일은 Kaggle Dataset으로 올려 /kaggle/input/ 아래에서 찾음
#   - T4 x2 중 1장만 사용 (Unsloth는 2장일 때 오히려 느림)
# 셀 단위(# %%)로 나눠 두었다. Kaggle에서는 train/finetune_kaggle.ipynb 를 Import 하면 셀이 그대로 들어간다.
# 3시간 가까이 걸리므로 편집 화면에서 직접 돌리지 말고 "Save Version -> Save & Run All"로 실행한다
# (편집 화면은 20분 동안 아무 입력이 없으면 끊긴다).
# 첫 Kaggle 실행(2026-10-06)은 step 80부터 Loss가 nan이 되어 사실상 학습되지 않았다. 그래서
#   - padding_free를 끄고 (Unsloth가 자동으로 켜던 기능, 가장 유력한 원인)
#   - Loss를 로그에 한 줄씩 찍고, nan이 나오면 즉시 멈추며
#   - TEST_STEPS로 앞부분만 먼저 돌려 확인한 뒤 본 학습을 한다.

# %% 0. GPU 1장만 쓰도록 설정 (torch를 불러오기 전에 해야 함) + GPU 확인
import os

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# !nvidia-smi

# %% 1. 설치
# !pip install unsloth

# %% 2. 실행 이름과 파일 위치
import glob

TEST_STEPS = 150  # 시험 실행: 이 단계에서 멈추고 저장은 건너뜀. 본 학습은 0으로 바꾼다
RUN = "v3"  # 실행마다 다른 이름을 쓴다 (Kaggle은 Version마다 결과가 따로 남지만, 파일 이름으로도 구분)
DATA_NAME = {
    "v1": "train.jsonl",
    "v2": "train_v2.jsonl",
    "v3": "train_v3.jsonl",
    "v4": "train_v4.jsonl",  # v3 + 오류 수정 대화 (scripts/gen_fix_dialogs.py)
}[RUN]
# Dataset 이름을 무엇으로 지었든 /kaggle/input 아래에서 파일 이름으로 찾는다
found = glob.glob(f"/kaggle/input/**/{DATA_NAME}", recursive=True)
assert found, f"{DATA_NAME}을 찾지 못함. 오른쪽 Input에 Dataset을 추가했는지 확인하세요."
DATA_FILE = found[0]
OUT_DIR = f"/kaggle/working/{RUN}"  # 여기 저장한 것만 실행 후 남는다
TMP_DIR = "/tmp/work"  # 체크포인트, GGUF 중간 파일 (수 GB라 저장하지 않는 곳에 둠)
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)
print("학습 파일:", DATA_FILE)

# %% 3. 모델 로드 (4bit)
from unsloth import FastLanguageModel  # noqa: I001  (unsloth는 transformers보다 먼저 불러와야 함)

import torch
import transformers
import trl
import unsloth

# 환경이 바뀌면 결과가 달라질 수 있어 버전을 로그에 남긴다
print(f"unsloth {unsloth.__version__} / transformers {transformers.__version__} / trl {trl.__version__} / torch {torch.__version__}")

MODEL_NAME = "unsloth/Qwen2.5-Coder-3B-Instruct"
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

ds = load_dataset("json", data_files=DATA_FILE, split="train")
ds = ds.map(lambda ex: {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False)})
# 스키마가 너무 길어 잘리는 샘플 제외
ds = ds.filter(lambda ex: len(tokenizer(ex["text"]).input_ids) <= MAX_SEQ_LEN)
print(ds)

# %% 5. 학습 (T4는 bf16 미지원 → fp16)
import math
import time

from transformers import TrainerCallback
from trl import SFTConfig, SFTTrainer
from unsloth.chat_templates import train_on_responses_only


class Monitor(TrainerCallback):
    """Kaggle 로그에는 학습 진행 표가 안 보이므로 Loss를 직접 출력하고, nan이면 바로 멈춘다."""

    def __init__(self):
        self.bad_step = None
        self.t0 = time.time()

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs or "loss" not in logs:
            return
        step, total, loss = state.global_step, state.max_steps, logs["loss"]
        mins = (time.time() - self.t0) / 60
        left = mins / max(step, 1) * (total - step)
        print(f"step {step}/{total}  loss {loss:.4f}  grad_norm {logs.get('grad_norm')}  "
              f"경과 {mins:.0f}분, 남은 시간 약 {left:.0f}분", flush=True)
        if not math.isfinite(loss):
            self.bad_step = step
            control.should_training_stop = True

    def on_step_end(self, args, state, control, **kwargs):
        if TEST_STEPS and state.global_step >= TEST_STEPS:
            control.should_training_stop = True  # 학습률 일정은 본 학습과 같게 두고 앞부분만 본다


monitor = Monitor()

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
        output_dir=f"{TMP_DIR}/checkpoints",
        report_to="none",
        padding_free=False,
    ),
    callbacks=[monitor],
)
# 손실은 SQL(assistant 응답) 부분에만 계산 — 스키마를 외우는 데 용량을 쓰지 않도록
trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)

# 오류 수정 대화(v4)는 assistant 턴이 둘이라 틀린 SQL을 배우지 않게 마지막 응답만 남긴다.
# assistant 턴이 하나인 일반 예시(v3까지)는 그대로다.
RESP_IDS = tokenizer.encode("<|im_start|>assistant\n", add_special_tokens=False)


def last_response_only(ex):
    ids, labels = ex["input_ids"], list(ex["labels"])
    n = len(RESP_IDS)
    starts = [i for i in range(len(ids) - n + 1) if ids[i : i + n] == RESP_IDS]
    if len(starts) > 1:
        cut = starts[-1] + n
        labels[:cut] = [-100] * cut
    return {"labels": labels}


trainer.train_dataset = trainer.train_dataset.map(last_response_only)
trainer.train()

if monitor.bad_step is not None:
    raise RuntimeError(f"step {monitor.bad_step}에서 Loss가 nan이 되어 멈춤. 결과를 저장하지 않습니다.")
if TEST_STEPS:
    print(f"시험 실행 정상 종료 (step {TEST_STEPS}까지 nan 없음). TEST_STEPS = 0 으로 바꿔 본 학습을 실행하세요.")

# %% 6. LoRA 어댑터 + Loss 기록 저장 (GGUF 변환이 실패해도 학습 결과는 보존)
if not TEST_STEPS:  # 시험 실행이면 저장하지 않음
    with open(f"{OUT_DIR}/loss_table.txt", "w") as f:  # scripts/plot_loss.py 가 읽는 형식
        f.write("Step\tTraining Loss\n")
        for h in trainer.state.log_history:
            if "loss" in h:
                f.write(f"{h['step']}\t{h['loss']:.6f}\n")

    model.save_pretrained(f"{OUT_DIR}/lora_adapter")
    tokenizer.save_pretrained(f"{OUT_DIR}/lora_adapter")
    print("LoRA 저장 완료:", f"{OUT_DIR}/lora_adapter")

# %% 7. Ollama용 GGUF 변환 (중간 파일은 /tmp에, q4_k_m GGUF만 /kaggle/working으로)
if not TEST_STEPS:  # 시험 실행이면 저장하지 않음
    import shutil

    model.save_pretrained_gguf(f"{TMP_DIR}/gguf_out", tokenizer, quantization_method="q4_k_m")

    # Unsloth 버전에 따라 결과가 gguf_out_gguf/ 같은 폴더에 생기기도 해서 넓게 찾는다
    all_ggufs = glob.glob(f"{TMP_DIR}/**/*.gguf", recursive=True) + glob.glob("/kaggle/working/*.gguf")
    for p in all_ggufs:
        print(f"{os.path.getsize(p) / 1e9:6.2f} GB  {p}")
    keep = [p for p in all_ggufs if "q4_k_m" in os.path.basename(p).lower()]
    assert keep, "q4_k_m GGUF를 찾지 못함 (위 목록 확인)"

    os.makedirs(f"{OUT_DIR}/gguf_out", exist_ok=True)
    for p in keep:
        if not p.startswith(OUT_DIR):
            shutil.move(p, f"{OUT_DIR}/gguf_out/{os.path.basename(p)}")
    # /kaggle/working 바로 아래에 다른 GGUF가 생겼다면 지워 20GB 한도와 다운로드 크기를 아낀다
    for p in glob.glob("/kaggle/working/*.gguf"):
        os.remove(p)

    for root, _, files in os.walk(OUT_DIR):
        for name in files:
            p = os.path.join(root, name)
            print(f"{os.path.getsize(p) / 1e6:9.1f} MB  {p}")
    # 끝나면 Version 화면의 Output 탭에서 v3/gguf_out/*.gguf 를 내려받아 models/v3/ 에 두고 로컬에서:
    #   ollama create text2sql-ft-v3 -f models/v3/Modelfile
