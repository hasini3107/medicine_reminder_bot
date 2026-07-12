from utils.ocr_helper import extract_text_from_file
from utils.prescription_parser import parse_prescription_text
import json

filepath = 'uploads/prescriptions/guest_ChatGPT_Image_Jul_10_2026_03_09_21_PM.png'
try:
    text = extract_text_from_file(filepath)
    meds = parse_prescription_text(text)
    with open('scripts/debug_parse_output.txt','w',encoding='utf-8') as f:
        f.write('---TEXT---\n')
        f.write(text or '')
        f.write('\n---MEDS---\n')
        f.write(json.dumps(meds, indent=2, ensure_ascii=False))
    print('WROTE scripts/debug_parse_output.txt')
except Exception as e:
    import traceback
    traceback.print_exc()
    with open('scripts/debug_parse_output.txt','w',encoding='utf-8') as f:
        f.write('ERROR:\n')
        f.write(str(e))
