import json

with open('all_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# حفظ الملف بدون مسافات أو أسطر جديدة (يقلل الحجم بنسبة 20-30%)
with open('all_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))