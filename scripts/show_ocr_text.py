from utils.ocr_helper import extract_text_from_file
fp='uploads/prescriptions/guest_ChatGPT_Image_Jul_10_2026_03_09_21_PM.png'
text = extract_text_from_file(fp)
print('LEN', len(text))
print(text)
