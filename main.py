import json
import os
from datetime import datetime

def combine_and_paginate_json():
    combined_data = []
    output_file = 'all_data.json'
    db_dir = 'db' # المجلد الذي سيحتوي على التقسيمات
    pages_dir = os.path.join(db_dir, 'pages')
    
    # التأكد من وجود المجلدات
    if not os.path.exists(pages_dir):
        os.makedirs(pages_dir)

    # 1. الترتيب المفضل للمصادر
    priority_order = ["fushaar", "akoam", "laroza", "mycima", "egibest"]
    
    # جلب ملفات الـ JSON (تجنب الملفات الناتجة والملفات المخفية)
    all_files = [f for f in os.listdir('.') if f.endswith('.json') 
                 and f not in [output_file, 'manifest.json'] 
                 and not f.startswith('.')]
    
    ordered_files = []
    # ترتيب الملفات بناءً على الأولية
    for keyword in priority_order:
        temp_list = [f for f in all_files if keyword in f.lower()]
        ordered_files.extend(temp_list)
        for f in temp_list: all_files.remove(f)
    
    ordered_files.extend(all_files) # إضافة الباقي

    # 2. عملية الدمج
    for file in ordered_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    combined_data.extend(data)
                    print(f"✅ تم دمج {len(data)} عنصر من {file}")
        except Exception as e:
            print(f"❌ خطأ في {file}: {e}")

    if not combined_data:
        print("ℹ️ لا توجد بيانات للعمل عليها.")
        return

    # --- الجزء الجديد: التقسيم والضغط للسلاسة التامة ---

    # 3. حفظ النسخة الكاملة (مضغوطة وبدون مسافات لتوفير المساحة)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False) # حذفنا indent=4 لتصغير الحجم

    # 4. تقسيم البيانات إلى صفحات (كل صفحة 300 عنصر)
    page_size = 300
    total_items = len(combined_data)
    total_pages = (total_items // page_size) + (1 if total_items % page_size > 0 else 0)

    for i in range(0, total_items, page_size):
        page_num = (i // page_size) + 1
        chunk = combined_data[i : i + page_size]
        with open(f'{pages_dir}/{page_num}.json', 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False) # حفظ الصفحة مضغوطة

    # 5. إنشاء ملف الـ Manifest (الفهرس) الذي يطلبه كود فلاتر
    manifest = {
        "total_pages": total_pages,
        "total_items": total_items,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "page_size": page_size
    }
    with open(os.path.join(db_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n🏁 تم الدمج والتقسيم بنجاح!")
    print(f"📦 الإجمالي: {total_items} عنصر.")
    print(f"📄 عدد الصفحات: {total_pages} صفحة في مجلد 'db/pages'.")
    print(f"🚀 تم ضغط ملف {output_file} لضمان أفضل أداء.")

if __name__ == "__main__":
    combine_and_paginate_json()