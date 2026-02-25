import json
import glob

def combine_all_json():
    combined_data = []
    output_file = 'all_data.json'
    
    # جلب كل ملفات الـ JSON في المجلد الحالي
    all_json_files = glob.glob("*.json")
    
    # تصفية الملفات: استبعاد الملف النهائي وأي ملفات مخفية
    json_files_to_read = [
        f for f in all_json_files 
        if f != output_file and not f.startswith('.')
    ]
    
    print(f"📂 جاري دمج الملفات التالية: {json_files_to_read}")

    for file in json_files_to_read:
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
        print(f"🏁 تم إنشاء الملف الجامع بنجاح: {output_file} بإجمالي {len(combined_data)} عنصر.")
    else:
        print("ℹ️ لا توجد بيانات لدمجها.")

if __name__ == "__main__":
    combine_all_json()