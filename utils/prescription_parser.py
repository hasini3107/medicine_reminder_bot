import json
import requests
from config import OLLAMA_URL, MODEL_NAME, OLLAMA_TIMEOUT
from utils.medicine_helper import medicines as DATASET_MEDICINES, _normalize_text

def parse_prescription_text(extracted_text: str) -> list:
    """
    Sends the extracted prescription text to Ollama and expects a JSON list of medicines.
    Returns a list of dictionary objects.
    """
    if not extracted_text.strip():
        return []

    prompt = f"""You are a medical data extractor. Extract the medicines from the following prescription text.
Return ONLY a valid JSON array of objects. Do not include any markdown formatting, explanations, or backticks.
Each object should have the following keys:
- "name" (string, the medicine name and strength, e.g., "Paracetamol 500mg")
- "generic" (string, the generic name if found or known, otherwise "")
- "dosage" (string, e.g., "1 Tablet")
- "when" (string, e.g., "After Food", "Morning", etc.)
- "uses" (string, briefly what it is used for based on general knowledge)
- "status" (string, always "Active")

Prescription Text:
{extracted_text}
"""
    
    try:
        response = _post_to_ollama({
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        })
        result = response.json()
        response_text = _extract_ollama_text(result) or result.get("response", "[]").strip()
        
        # Clean up in case model ignored 'no markdown'
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
            
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        parsed_data = json.loads(response_text.strip())
        
        # Sometimes models wrap in an object instead of pure list
        if isinstance(parsed_data, dict):
            for key, val in parsed_data.items():
                if isinstance(val, list):
                    return val
            return [parsed_data]
            
        if isinstance(parsed_data, list):
            return parsed_data
            
        return []
    except Exception as e:
        print(f"[ERROR] Ollama extraction failed: {e}")
        # Fallback: try a simple dataset-based extractor to find medicine names mentioned in the text
        try:
            found = []
            txt_norm = _normalize_text(extracted_text)
            seen = set()
            for med in DATASET_MEDICINES:
                name = str(med.get("Medicine Name", "") or "").strip()
                generic = str(med.get("Generic Name", "") or "").strip()
                if not name and not generic:
                    continue
                name_norm = _normalize_text(name)
                generic_norm = _normalize_text(generic)
                if name_norm and name_norm in txt_norm and name_norm not in seen:
                    seen.add(name_norm)
                    found.append({
                        "name": name,
                        "generic": generic,
                        "dosage": med.get("Dosage", ""),
                        "when": med.get("When to Take", ""),
                        "uses": med.get("Uses", ""),
                        "status": "Active",
                    })
                elif generic_norm and generic_norm in txt_norm and generic_norm not in seen:
                    seen.add(generic_norm)
                    found.append({
                        "name": name,
                        "generic": generic,
                        "dosage": med.get("Dosage", ""),
                        "when": med.get("When to Take", ""),
                        "uses": med.get("Uses", ""),
                        "status": "Active",
                    })
            return found
        except Exception as e2:
            print(f"[ERROR] Local parsing fallback failed: {e2}")
            return []


def _extract_ollama_text(payload: dict) -> str:
    if not isinstance(payload, dict):
        return ""

    if isinstance(payload.get("response"), str) and payload["response"].strip():
        return payload["response"].strip()

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

    if isinstance(payload.get("output"), str):
        return payload["output"].strip()

    if isinstance(payload.get("text"), str):
        return payload["text"].strip()

    return ""


def _post_to_ollama(payload: dict):
    candidates = [OLLAMA_URL]
    if OLLAMA_URL.endswith("/api/generate"):
        candidates.append(OLLAMA_URL.replace("/api/generate", "/v1/generate"))
    elif OLLAMA_URL.endswith("/v1/generate"):
        candidates.append(OLLAMA_URL.replace("/v1/generate", "/api/generate"))
    else:
        base = OLLAMA_URL.rstrip("/")
        candidates.extend([f"{base}/v1/generate", f"{base}/api/generate"])

    last_error = None
    for url in candidates:
        try:
            response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
            response.raise_for_status()
            return response
        except requests.HTTPError as exc:
            last_error = exc
            status = getattr(exc.response, 'status_code', None)
            if status in {404, 405}:
                continue
            raise
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f"Failed to reach Ollama via {candidates}: {last_error}")
