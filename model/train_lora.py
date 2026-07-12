# ============================================================
# model/train_lora.py
#
# LoRA fine-tuning script for the MediAssist AI model.
#
# Run from the project root:
#   py -3 model/train_lora.py
#
# Requirements: torch, transformers, peft
#   pip install torch transformers peft
#
# Output: saves LoRA adapter weights to ./lora_adapter/
# ============================================================

import json
import sys
import os

# Allow imports relative to project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

from config import DATASET_FILE, MODEL_NAME


# ------------------------------------------------------------------
# 1. Load & format dataset
# ------------------------------------------------------------------
print(f"[INFO] Loading dataset from: {DATASET_FILE}")
with open(DATASET_FILE, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

training_data = []
for entry in raw_data:
    name         = entry.get("Medicine Name", "").strip()
    generic      = entry.get("Generic Name",  "").strip()
    uses         = entry.get("Uses",          "").strip()
    dosage       = entry.get("Dosage",        "").strip()
    side_effects = entry.get("Side Effects",  "").strip()
    precautions  = entry.get("Precautions",   "").strip()
    when         = entry.get("When to Take",  "").strip()

    if not name or not uses:
        continue

    prompt = (
        f"What are the uses, dosage, side effects, precautions, "
        f"and when to take {name}?"
    )

    answer = f"""🔍 **Information:** {name} (generic: {generic}) is a medication \
commonly used to treat or manage: {uses}.

📋 **Uses:**
{uses}

💊 **Dosage:**
{dosage or 'N/A'}

⚠️ **Side Effects:**
{side_effects or 'N/A'}

🛡️ **Precautions:**
{precautions or 'N/A'}

⏰ **Reminder Time (When to Take):**
{when or 'N/A'}"""

    training_data.append({"question": prompt, "answer": answer})

print(f"[INFO] Prepared {len(training_data)} training examples.")


# ------------------------------------------------------------------
# 2. Load model & tokeniser
# ------------------------------------------------------------------
print(f"[INFO] Loading model: {MODEL_NAME}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)


# ------------------------------------------------------------------
# 3. Apply LoRA
# ------------------------------------------------------------------
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()


# ------------------------------------------------------------------
# 4. Training loop
# ------------------------------------------------------------------
optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
EPOCHS    = 3

for epoch in range(EPOCHS):
    epoch_loss = 0.0
    for entry in training_data:
        inputs = tokenizer(entry["question"], return_tensors="pt")
        labels = tokenizer(entry["answer"],   return_tensors="pt").input_ids

        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        labels = labels.to(model.device)

        outputs = model(**inputs, labels=labels)
        loss    = outputs.loss

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        epoch_loss += loss.item()

    avg = epoch_loss / len(training_data)
    print(f"[Epoch {epoch + 1}/{EPOCHS}] avg loss: {avg:.4f}")


# ------------------------------------------------------------------
# 5. Save LoRA adapter
# ------------------------------------------------------------------
SAVE_PATH = "lora_adapter"
model.save_pretrained(SAVE_PATH)
print(f"[INFO] LoRA adapter saved → ./{SAVE_PATH}/")
