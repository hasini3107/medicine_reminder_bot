from app import create_app

app = create_app()

with app.test_client() as c:
    try:
        resp = c.post('/api/reports/parse-report', json={'filename': 'ChatGPT Image Jul 10, 2026, 03_09_21 PM.png'})
        print(resp.status_code)
        print(resp.get_data(as_text=True))
    except Exception as e:
        import traceback
        traceback.print_exc()
