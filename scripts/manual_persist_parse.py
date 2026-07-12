import json, os
from utils.ocr_helper import extract_text_from_file
from utils.prescription_parser import parse_prescription_text

UPLOAD_PATH = 'uploads/prescriptions/guest_ChatGPT_Image_Jul_10_2026_03_09_21_PM.png'
MED_FILE = 'data/user_medicines.json'
REM_FILE = 'data/user_reminders.json'
REPORT_FILE = 'data/user_reports.json'
USER = 'guest'

text = extract_text_from_file(UPLOAD_PATH)
meds = parse_prescription_text(text)
print('PARSED MEDS:', meds)

# Load medicines
if os.path.exists(MED_FILE):
    with open(MED_FILE,'r',encoding='utf-8') as f:
        meds_data = json.load(f)
else:
    meds_data = {}
user_meds = meds_data.get(USER, [])
current_max = max([m.get('id',0) for m in user_meds]) if user_meds else 0
added = []
for m in meds:
    current_max += 1
    m['id'] = current_max
    m.setdefault('status','Active')
    user_meds.append(m)
    added.append(m)
meds_data[USER] = user_meds
with open(MED_FILE,'w',encoding='utf-8') as f:
    json.dump(meds_data,f,indent=2,ensure_ascii=False)

# Load reminders and add defaults
if os.path.exists(REM_FILE):
    with open(REM_FILE,'r',encoding='utf-8') as f:
        rem_data = json.load(f)
else:
    rem_data = {}
user_rems = rem_data.get(USER, [])
rem_max = max([r.get('id',0) for r in user_rems]) if user_rems else 0
created = []
for m in added:
    rem_max += 1
    rem = {
        'id': rem_max,
        'medId': m['id'],
        'medName': m.get('name',''),
        'time': '09:00',
        'done': False,
        'note': 'Auto-created from manual script'
    }
    user_rems.append(rem)
    created.append(rem)
rem_data[USER] = user_rems
with open(REM_FILE,'w',encoding='utf-8') as f:
    json.dump(rem_data,f,indent=2,ensure_ascii=False)

print(f'Added {len(added)} medicines and {len(created)} reminders')
print('WROTE', MED_FILE, REM_FILE)
