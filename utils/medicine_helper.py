# ============================================================
# utils/medicine_helper.py
#
# Responsibilities:
#   1. Load the medicine dataset from disk (once, at import time).
#   2. Provide get_specific_answer() — keyword-based lookup that
#      returns a structured reply without calling the AI model.
# ============================================================

import json
import os
import re

from config import DATASET_FILE


# ------------------------------------------------------------------
# 1. Dataset loading
# ------------------------------------------------------------------
def _load_medicines():
    """Load and sanitise the medicine JSON dataset."""
    if not os.path.exists(DATASET_FILE):
        print(f"[WARNING] Dataset not found at: {DATASET_FILE}")
        return []

    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    data = [m for m in data if m]
    print(f"[INFO] Loaded {len(data)} medicine records from dataset.")
    return data


medicines = _load_medicines()


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


# ------------------------------------------------------------------
# 2. Keyword-based structured answer (fast path, no AI needed)
# ------------------------------------------------------------------
def get_specific_answer(medicine: dict, query: str) -> str:
    """Return a focused answer for a known medicine based on the user's intent."""
    query_lower = query.lower()

    med_name = str(medicine.get("Medicine Name") or "N/A")
    gen_name = str(medicine.get("Generic Name") or "N/A")
    uses = str(medicine.get("Uses") or "N/A")
    dosage = str(medicine.get("Dosage") or "N/A")
    side_effects = str(medicine.get("Side Effects") or "N/A")
    precautions = str(medicine.get("Precautions") or "N/A")
    when = str(medicine.get("When to Take") or "N/A")

    is_uses = any(
        kw in query_lower
        for kw in ["use", "purpose", "treat", "cure", "help with", "for what", "why do", "indicated"]
    )
    is_dosage = any(
        kw in query_lower
        for kw in ["dosage", "dose", "how much", "quantity", "amount", "mg"]
    )
    is_side_effects = any(
        kw in query_lower
        for kw in ["side effect", "sideeffect", "adverse", "reaction", "harmful", "symptom", "cause", "causes", "caused"]
    )
    is_precautions = any(
        kw in query_lower
        for kw in ["precaution", "caution", "avoid", "safe", "safety", "warning", "risk"]
    )
    is_when = any(
        kw in query_lower
        for kw in ["when to take", "when should", "time to take", "schedule", "reminder", "when do", "before food", "after food", "with meals"]
    )
    is_storage = any(
        kw in query_lower
        for kw in ["store", "storage", "keep", "temperature", "room temperature"]
    )
    is_children = any(
        kw in query_lower
        for kw in ["children", "child", "kids", "pediatric", "paediatric"]
    )

    if is_when:
        return f"⏰ **Reminder:** {med_name} should be taken **{when}**."
    if is_children:
        return (
            f"👶 **Children:** This dataset does not include pediatric-specific guidance for {med_name}. "
            "Please consult a qualified healthcare professional before giving this medicine to a child."
        )
    if is_side_effects:
        return f"⚠️ **Side Effects:** Common side effects of {med_name} include: **{side_effects}**."
    if is_precautions:
        return f"🛡️ **Precautions:** When taking {med_name}, keep in mind: **{precautions}**."
    if is_storage:
        return f"📦 **Storage:** Follow the medicine packaging instructions for {med_name}. If there is no storage label, keep it in a cool, dry place away from direct sunlight and moisture."
    if is_dosage:
        return f"💊 **Dosage:** The standard dosage for {med_name} is **{dosage}**."
    if is_uses:
        return f"📋 **Uses:** {med_name} is used for **{uses}**."

    return (
        f"{med_name} (generic: {gen_name}) is typically used for {uses}. "
        "If you want a specific detail, please ask about dosage, side effects, precautions, or when to take it."
    )

# ------------------------------------------------------------------
# 3. Medicine name matching helper (used by chat route)
# ------------------------------------------------------------------
def find_medicine_in_query(user_message: str):
    """Scan the dataset for a medicine whose name or generic name appears in the query."""
    msg_norm = _normalize_text(user_message)
    if not msg_norm:
        return None

    weak_generic_terms = {
        "alcohol", "water", "saline", "soap", "lotion", "cream", "gel", "oil", "hand sanitizer", "sanitizer"
    }
    weak_medicine_terms = {
        "hand sanitizer", "sanitizer", "alcohol", "water", "saline", "soap", "lotion", "cream", "gel", "oil", "perfume"
    }

    for medicine in medicines:
        name = str(medicine.get("Medicine Name", ""))
        generic = str(medicine.get("Generic Name", ""))
        clean_name = _normalize_text(re.sub(r"\(.*?\)", "", name))
        clean_generic = _normalize_text(re.sub(r"\(.*?\)", "", generic))

        compact_name = re.sub(r"[^a-z0-9]", "", clean_name)
        compact_generic = re.sub(r"[^a-z0-9]", "", clean_generic)
        compact_query = re.sub(r"[^a-z0-9]", "", msg_norm)

        generic_is_weak = clean_generic in weak_generic_terms or compact_generic in weak_generic_terms
        name_is_weak = any(term in clean_name for term in weak_medicine_terms) or any(term in compact_name for term in weak_medicine_terms)
        if generic_is_weak or name_is_weak:
            continue

        name_in_query = clean_name and clean_name in msg_norm

        if (clean_name and clean_name in msg_norm) or \
           (clean_generic and clean_generic in msg_norm and not generic_is_weak) or \
           (compact_name and compact_name in compact_query) or \
           (compact_generic and compact_generic in compact_query and not generic_is_weak):
            return medicine

        # Match when all medicine tokens appear in the query, in any order.
        name_tokens = [token for token in clean_name.split() if len(token) > 1]
        generic_tokens = [token for token in clean_generic.split() if len(token) > 1]
        query_tokens = msg_norm.split()

        if name_tokens and all(token in query_tokens for token in name_tokens):
            return medicine
        if generic_tokens and all(token in query_tokens for token in generic_tokens):
            return medicine

    return None
