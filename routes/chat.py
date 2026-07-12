# ============================================================
# routes/chat.py
#
# Responsibility: Handle POST /chat requests.
#   1. Search the local medicine dataset first (fast, no AI).
#   2. Fall back to Ollama AI model for everything else.
# ============================================================

import re
import requests
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify

from config import OLLAMA_URL, MODEL_NAME, OLLAMA_TIMEOUT
from utils.medicine_helper import find_medicine_in_query, get_specific_answer

chat_bp = Blueprint("chat", __name__)

MEDICAL_KEYWORDS = (
    "medicine",
    "medication",
    "drug",
    "dosage",
    "dose",
    "side effect",
    "side effects",
    "precaution",
    "precautions",
    "symptom",
    "symptoms",
    "disease",
    "health",
    "pain",
    "fever",
    "allergy",
    "diabetes",
    "blood pressure",
    "treatment",
    "doctor",
    "prescription",
    "tablet",
    "capsule",
    "pill",
    "syrup",
    "ointment",
    "injection",
    "cold",
    "viral",
    "highbp",
    "lowbp",
    "headache",
    "drowsiness",
    "sleepiness",
    "nausea",
    "rash",
    "cough",
    "infection",
    "infections",
    "parasite",
    "parasites",
    "interaction",
    "alcohol",
    "storage",
    "temperature",
    "safety",
    "safe",
    "diet",
    "food",
    "spicy",
    "antibiotic",
    "antibiotics",
    "heat",
    "fever",
    "immune",
    "nutrition",
    "hydration",
    "exercise",
    "fitness",
    "workout",
    "sleep",
    "stress",
    "mental",
    "anxiety",
    "depression",
    "weight",
)

MEDICAL_PATTERNS = (
    "what is",
    "what are",
    "tell me about",
    "tell about",
    "can children",
    "is it safe",
    "should i",
    "how do i",
    "how to",
    "when should",
    "when to",
    "what should i",
    "does",
    "do i",
    "can we",
    "could i",
    "would it be",
    "is it okay",
    "should i",
    "any side effects",
    "how much",
    "how to improve",
    "how to reduce",
    "tips for",
)


# ------------------------------------------------------------------
# POST /chat
# ------------------------------------------------------------------
@chat_bp.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        user_message = str(data.get("message", "")).strip()

        if not user_message:
            return jsonify({"reply": "Please enter a message."})

        if len(user_message) > 1000:
            return jsonify({"reply": "Please keep your question shorter so I can answer it clearly."})

        # ── Step 1: Try local dataset match (instant response) ──
        medicine = find_medicine_in_query(user_message)
        if medicine:
            reply = get_specific_answer(medicine, user_message)
            return jsonify({"reply": reply})

        if not _looks_medical(user_message):
            return jsonify({
                "reply": "I can help with medicines, general health and wellness tips (diet, exercise, sleep, stress), and medication guidance. For diagnosis or treatment decisions, please consult a qualified healthcare professional."
            })

        # ── Step 2: Ask Ollama AI model ──────────────────────────
        prompt = _build_prompt(user_message)

        try:
            response = _post_to_ollama({
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
            })
            reply = None

            try:
                result = response.json()
            except ValueError:
                result = {"response": response.text}

            if isinstance(result, dict):
                reply = _extract_ollama_text(result)

            if not reply:
                reply = response.text.strip()

            if not reply:
                raise ValueError("Empty response from Ollama")

            return jsonify({"reply": _sanitize_reply(reply)})
        except Exception as exc:
            print(f"[ERROR] /chat → {exc}")
            # Try to generate a safe local reply for common health/wellness questions
            local = _local_health_advice(user_message)
            return jsonify({"reply": _sanitize_reply(local)})

    except Exception as exc:
        print(f"[ERROR] /chat → {exc}")
        return jsonify({"reply": f"Server Error: {str(exc)}"})


# ------------------------------------------------------------------
# Internal helper — keeps the route handler clean
# ------------------------------------------------------------------
def _looks_medical(user_message: str) -> bool:
    text = user_message.lower()

    # Accept direct medical keywords and common condition terms.
    if any(keyword in text for keyword in MEDICAL_KEYWORDS):
        return True

    # Accept medical questions even when keyword coverage is not exact.
    if any(pattern in text for pattern in MEDICAL_PATTERNS):
        return True

    # Recognize common medical terms that may appear without explicit keywords.
    medical_signals = (
        "pill", "tablet", "capsule", "syrup", "ointment", "injection",
        "prescription", "dose", "dosage", "side effect", "allergy",
        "headache", "nausea", "dizziness", "infection", "infections",
        "fever", "cough", "pain", "blood pressure", "diabetes",
        "cholesterol", "asthma", "anxiety", "depression", "arthritis",
        "migraine", "cold", "flu", "treatment", "medication",
        "antibiotic", "antibiotics", "parasite", "parasites", "food",
        "diet", "spicy", "alcohol", "heat", "storage", "temperature"
    )
    if any(signal in text for signal in medical_signals):
        return True

    return False


def _build_prompt(user_message: str) -> str:
    """Build the system + user prompt sent to Ollama."""
    return f"""You are MediAssist, a safe and empathetic medical assistant.
Your job is to provide accurate, simple, and helpful information about medicines, general health, and wellness topics.

Rules:
- Answer only medicine and health-related questions.
- If the user asks about a medicine, answer only the specific question they asked.
- If the question is about a medicine that is not in the local dataset, provide a helpful Ollama-based answer.
- Fail safely: if the question is not medical or health-related, decline politely and do not attempt to answer.
- Do not provide a full medication profile unless the user specifically requests all details.
- Keep your response concise, direct, and focused on the requested topic.
- For general health and wellness questions (diet, exercise, sleep, stress, mental health, weight management), provide brief, practical, non-prescriptive tips and clearly label them as general guidance.
- Do not diagnose diseases, prescribe treatments, or give medical instructions that require a qualified practitioner.
- If information is uncertain, state that it should be verified with a healthcare professional.

User Query: {user_message}
"""


def _sanitize_reply(reply: str) -> str:
    cleaned = reply.strip()
    if not cleaned:
        return cleaned
    if not cleaned.lower().startswith(("i'm", "i am", "i can")):
        cleaned = f"{cleaned}\n\n⚠️ This information is for general guidance only and should be verified with a qualified healthcare professional."
    return cleaned


def _local_health_advice(user_message: str) -> str:
    """Return a short, safe, non-prescriptive health tip based on simple keywords/patterns.
    This is used as a fallback when Ollama is unavailable."""
    text = user_message.lower()

    # Dosage questions (general)
    if any(kw in text for kw in ("dosage", "dose of", "how much", "how many mg", "how many tablets", "what amount", "what's the dose", "what is the dose")):
        # Non-prescriptive guidance — direct user to check product leaflet / prescriber
        if "vitamin b12" in text or "b12" in text:
            return "Dosage depends on formulation and reason for use. Over-the-counter B12 supplements commonly range from a few hundred to 2,000 mcg daily; treatment or injection regimens differ. Check the product leaflet or follow your prescriber's instructions."
        return "Dosages vary by medicine, formulation, age and condition. Check the medicine leaflet or ask your pharmacist or prescriber for the exact dose for you."

    # Hydration / water
    if any(kw in text for kw in ("drink plenty", "plenty of water", "drink water", "stay hydrated")):
        return "Drinking enough fluids is generally helpful when taking many medicines; aim to sip water regularly unless your doctor advised fluid restriction."

    # Spicy food with antibiotics
    if "spicy" in text and "antibiotic" in text:
        return "Spicy food doesn't usually reduce antibiotic effectiveness, but it can worsen stomach upset in some people. If you feel gastrointestinal discomfort, prefer milder food and consult your prescriber."

    # Milk interactions
    if any(kw in text for kw in ("with milk", "take with milk", "milk")):
        return "Some medicines bind with calcium in milk and may be less effective (for example, some antibiotics). When in doubt, take the medicine with water and check the medicine leaflet or ask your pharmacist."

    # Extra / missed dose
    if any(kw in text for kw in ("extra dose", "taken extra", "accidentally take", "took an extra", "overdose", "taken too much", "take extra")):
        return "If you accidentally took an extra dose, check the medicine leaflet for overdose advice. For most medicines, a single extra dose may only cause mild effects; for severe symptoms (breathing difficulty, severe drowsiness, fainting, chest pain), seek urgent medical care or contact your local poison control center."

    # ORS / rehydration
    if any(kw in text for kw in ("ors", "oral rehydration", "after meals")):
        return "ORS can be taken to replace fluids and salts during dehydration. It may be sipped after meals or between meals; follow the product instructions. If vomiting persists or dehydration is severe, seek medical care."

    # Sleep / rest advice
    if any(kw in text for kw in ("sleep", "insomnia", "sleepy", "sleep better")):
        return "Good sleep habits help recovery: keep a regular sleep schedule, limit screens before bed, and create a dark, quiet sleeping environment."

    # Exercise / general fitness
    if any(kw in text for kw in ("exercise", "workout", "fitness")):
        return "Light-to-moderate activity is beneficial for most people; start gradually and discuss with your doctor if you have a chronic condition or take medications that affect heart rate or blood pressure."

    # Calcium timing
    if "calcium" in text:
        return "Calcium tablets are often taken with food to improve tolerance; calcium carbonate is better absorbed with meals while calcium citrate can be taken with or without food. Space calcium away from certain medicines (eg, some antibiotics, levothyroxine) — check the leaflet or ask a pharmacist."

    # Diet related
    if any(kw in text for kw in ("diet", "food", "eat")):
        return "Balanced meals with vegetables, lean proteins, whole grains and adequate fluids support recovery and medication tolerance. Avoid making major diet changes without consulting a healthcare professional."

    # Side effects / safety general advice
    if any(kw in text for kw in ("side effect", "side effects", "allergy", "allergic")):
        return "If you experience worrying side effects (difficulty breathing, swelling, severe rash, fainting), seek urgent medical care. For milder side effects, discuss alternatives with your prescriber."

    # Default fallback guidance
    return "I can provide general health and medicine information. For specific advice about medicines, dosages, or interactions, consult the medicine leaflet or a pharmacist/doctor."


def _extract_ollama_text(payload: dict) -> str:
    if not isinstance(payload, dict):
        return ""

    # Common top-level string fields returned by Ollama variants
    for field in ("response", "output", "text", "result", "answer"):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list):
            text_parts = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            if text_parts:
                return "\n".join(text_parts)

    # Some Ollama responses return a list of generated items under choices.
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"].strip()
            if isinstance(first_choice.get("text"), str):
                return first_choice["text"].strip()
            if isinstance(first_choice.get("output"), str):
                return first_choice["output"].strip()
            if isinstance(first_choice.get("response"), str):
                return first_choice["response"].strip()

    if isinstance(payload.get("data"), list):
        text_parts = [str(item).strip() for item in payload["data"] if isinstance(item, str) and item.strip()]
        if text_parts:
            return "\n".join(text_parts)

    return ""


def _post_to_ollama(payload: dict):
    parsed_url = urlparse(OLLAMA_URL)
    root = f"{parsed_url.scheme}://{parsed_url.netloc}"
    candidates = [OLLAMA_URL]

    if not OLLAMA_URL.endswith("/v1/generate") and not OLLAMA_URL.endswith("/api/generate"):
        candidates.extend([
            f"{root}/v1/generate",
            f"{root}/api/generate",
        ])

    # Use a small set of request body variants to support different Ollama API styles.
    prompt_text = payload.get("prompt")
    body_variants = [payload]
    if prompt_text:
        body_variants.append({**payload, "input": prompt_text, "prompt": None})
        body_variants.append({"model": payload.get("model"), "messages": [{"role": "user", "content": prompt_text}]})

    last_error = None
    for url in candidates:
        for body in body_variants:
            request_body = {k: v for k, v in body.items() if v is not None}
            try:
                response = requests.post(url, json=request_body, timeout=OLLAMA_TIMEOUT)
                response.raise_for_status()
                return response
            except requests.HTTPError as exc:
                last_error = exc
                status = getattr(exc.response, 'status_code', None)
                if status in {404, 405}:
                    break
                raise
            except Exception as exc:
                last_error = exc
                continue

    raise RuntimeError(f"Failed to reach Ollama via {candidates}: {last_error}")
