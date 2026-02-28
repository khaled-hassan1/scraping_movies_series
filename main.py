import json
import os

def combine_all_json():
    combined_data = []
    output_file = 'all_data.json'
    
    # 1. تحديد الترتيب الذي تريده (اسم الملف أو جزء منه)
    # تأكد أن الأسماء هنا تطابق أسماء الملفات التي تخرج من السكريبتات
    priority_order = [
        "fushaar",   # فشار أولاً
        "akoam",     # أكوام ثانياً
        "laroza"     # لاروزا ثالثاً
    ]
    
    # جلب كل ملفات الـ JSON الموجودة حالياً
    all_files = [f for f in os.listdir('.') if f.endswith('.json') and f != output_file and not f.startswith('.')]
    
    # 2. ترتيب الملفات بناءً على القائمة المحددة
    ordered_files = []
    
    # أولاً: أضف الملفات التي تتبع الترتيب المطلوب
    for keyword in priority_order:
        for f in all_files:
            if keyword in f.lower():
                ordered_files.append(f)
                all_files.remove(f) # إزالة من القائمة حتى لا يتكرر
    
    # ثانياً: أضف أي ملفات أخرى متبقية (مثل mycima, egibest الخ) في النهاية
    ordered_files.extend(all_files)
    
    print(f"📂 الترتيب النهائي للدمج: {ordered_files}")

    for file in ordered_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    combined_data.extend(data)
                    print(f"✅ تم إضافة {len(data)} عنصر من {file}")
                else:
                    print(f"⚠️ ملف {file} ليس بتنسيق List (تم تخطيه)")
        except Exception as e:
            print(f"❌ خطأ في قراءة الملف {file}: {e}")

    # حفظ الملف الجامع النهائي
    if combined_data:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)
        print(f"🏁 تم إنشاء الملف بنجاح بترتيبك الخاص بإجمالي {len(combined_data)} عنصر.")
    else:
        print("ℹ️ لا توجد بيانات لدمجها.")

if __name__ == "__main__":
    combine_all_json()