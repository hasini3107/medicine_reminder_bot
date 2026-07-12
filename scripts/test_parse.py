from utils.prescription_parser import parse_prescription_text
s='Paracetamol 500mg twice daily and Amoxicillin 500mg after meals'
try:
    res = parse_prescription_text(s)
    print('RES:', res)
    print('LEN:', len(res))
except Exception as e:
    print('EXC:', e)
    import traceback
    traceback.print_exc()
