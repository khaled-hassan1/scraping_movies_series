import json
import os

def generate_search_index():
    # 1. إعداد المسارات
    pages_dir = "db/pages"  # تأكد أن هذا هو مسار المجلد الذي يحتوي على الصفحات
    output_file = "db/search_index.json"
    
    search_index = []
    
    # التأكد من وجود المجلد
    if not os.path.exists(pages_dir):
        print(f"❌ خطأ: المجلد {pages_dir} غير موجود.")
        return

    # 2. الحصول على قائمة الملفات وترتيبها رقمياً
    # نفترض أن الملفات بأسماء مثل 1.json, 2.json ...
    page_files = [f for f in os.listdir(pages_dir) if f.endswith('.json')]
    # ترتيب الملفات رقمياً (1 ثم 2 ثم 3...) بدلاً من الترتيب النصي
    page_files.sort(key=lambda x: int(os.path.splitext(x)[0]))

    print(f"🔄 جاري معالجة {len(page_files)} صفحة...")

    # 3. المرور على كل صفحة واستخراج بيانات البحث فقط
    for filename in page_files:
        page_num = os.path.splitext(filename)[0]
        file_path = os.path.join(pages_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                page_items = json.load(f)
            
            for item in page_items:
                # نختار فقط الحقول الضرورية للبحث والعرض الأولي
                search_index.append({
                    "n": item.get("name", "Unknown"),      # n اختصار لـ name لتوفير المساحة
                    "y": item.get("year", 0),             # y اختصار لـ year
                    "g": item.get("genre", "عام"),        # g اختصار لـ genre
                    "img": item.get("image_url", ""),     # img للصورة
                    "p": int(page_num),                   # p رقم الصفحة للرجوع إليها لاحقاً
                    "u": item.get("url", "")              # u الرابط الأصلي لو احتجته
                })
        except Exception as e:
            print(f"⚠️ خطأ في معالجة الملف {filename}: {e}")

    # 4. حفظ الفهرس النهائي
    # استخدمنا indent=None و separators للحصول على أصغر حجم ملف ممكن (Minified)
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(search_index, f, ensure_ascii=False, separators=(',', ':'))
        
        # حساب حجم الملف الناتج للـ Log
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"✅ تم إنشاء الفهرس بنجاح!")
        print(f"📍 المسار: {output_file}")
        print(f"📊 عدد العناصر: {len(search_index)}")
        print(f"📦 حجم الملف: {file_size:.2f} MB")

    except Exception as e:
        print(f"❌ فشل حفظ ملف الفهرس: {e}")

if __name__ == "__main__":
    generate_search_index()