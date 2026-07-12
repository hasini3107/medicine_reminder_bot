import requests, json, sys

base = 'http://127.0.0.1:5000'
filename = 'ChatGPT Image Jul 10, 2026, 03_09_21 PM.png'

try:
    r = requests.post(f'{base}/api/reports/parse-report', json={'filename': filename}, timeout=30)
    print('PARSE_STATUS', r.status_code)
    try:
        print('PARSE_RESPONSE:', r.json())
    except Exception:
        print('PARSE_TEXT:', r.text)
except Exception as e:
    print('PARSE_ERROR', e)

for p in ['data/user_reports.json', 'data/user_medicines.json', 'data/user_reminders.json']:
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print('\nFILE:', p)
        print(json.dumps(data.get('guest', data), indent=2, ensure_ascii=False)[:2000])
    except Exception as e:
        print('READ_ERROR', p, e)
