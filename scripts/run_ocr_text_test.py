from app import create_app
import json

app = create_app()

with app.test_client() as c:
    try:
        resp = c.post('/api/reports/ocr-text', json={'filename': 'ChatGPT Image Jul 10, 2026, 03_09_21 PM.png'})
        out = {'status': resp.status_code, 'data': resp.get_data(as_text=True)}
        with open('scripts/ocr_debug.json', 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print('WROTE scripts/ocr_debug.json')
    except Exception:
        import traceback
        traceback.print_exc()
