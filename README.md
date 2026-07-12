# MediAssist — Medicine Reminder & AI Medical Assistant

MediAssist is a smart dashboard that combines interactive medicine tracking, customized reminders, performance reports, and an AI-powered explanation chatbot (backed by Ollama) to help users manage their medication schedules.

---

## 📂 Project Structure (current repo)

```text
medicine_reminder_bot/
├── app.py
├── config.py
├── requirements.txt
├── data/
│   ├── Final_Medicine_Dataset.json
│   ├── user_medicines.json
│   ├── user_profiles.json
│   ├── user_reminders.json
│   └── user_reports.json
├── model/                    # optional (training materials/scripts)
│   ├── README_LORA.md
│   └── train_lora.py
├── routes/
│   ├── __init__.py
│   ├── main.py               # GET / (dashboard)
│   ├── auth.py               # login/register/social endpoints
│   ├── chat.py               # POST /chat (dataset lookup + Ollama fallback)
│   └── data.py               # user data APIs
├── scripts/                 # optional (OCR/parse/dev test utilities)
├── static/
│   ├── css/
│   └── js/
├── templates/
│   ├── includes/
│   └── pages/
└── uploads/
    └── prescriptions/      # user uploaded prescription images (may be large)
└── utils/
    ├── __init__.py
    ├── medicine_helper.py
    ├── ocr_helper.py
    └── prescription_parser.py
```

---

## 🚀 Setup & Execution

### Prerequisites
- **Python 3.x**
- **Ollama** running locally

### Install dependencies
```bash
pip install -r requirements.txt
```

### Start the Flask app
```bash
py -3 app.py
```

Open in your browser: `http://127.0.0.1:5000/`

---

## 🤖 Ollama configuration
`config.py` uses:
- `OLLAMA_URL` (default: `http://localhost:11434/v1/generate`)
- `MODEL_NAME` (default: `mediassist-finetuned`)

If your Ollama model differs, set environment variables or update `config.py`.

---

## 🤖 LoRA Fine-Tuning (Optional)
To fine-tune a model on the local dataset with LoRA:
```bash
py -3 model/train_lora.py
```

This requires `torch`, `transformers`, and `peft` packages.

