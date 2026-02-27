import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import os

# القيمة الافتراضية None تعني سحب كافة الصفحات المتاحة
async def scrape_egibest_series(max_pages=None):
    all_series = [] 
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # منع الصور لتسريع العملية
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            current_page = 1
            while True:
                # التحقق من شرط التوقف إذا تم تحديد عدد صفحات معين
                if max_pages is not None and current_page > max_pages:
                    break

                url = f"https://egibest.live/series/page/{current_page}/"
                print(f"📡 جاري سحب مسلسلات إيجي بست (صفحة {current_page})...")
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    # إذا كانت الصفحة غير موجودة (نهاية المحتوى)
                    if response.status == 404:
                        print(f"🏁 تم الوصول لنهاية الصفحات عند الصفحة {current_page - 1}")
                        break

                    await asyncio.sleep(2) # انتظار تحميل العناصر الديناميكية

                    # السيلكتور بناءً على بنية الموقع الحالية (postBlockCol)
                    items = await page.query_selector_all('a.postBlockCol')
                    
                    if not items:
                        print(f"🛑 لا توجد عناصر إضافية في صفحة {current_page}. انتهى السحب.")
                        break

                    for item in items:
                        try:
                            title_tag = await item.query_selector('h3.title')
                            title = await title_tag.inner_text() if title_tag else ""
                            
                            if not title or any(word in title.lower() for word in blacklist):
                                continue

                            href = await item.get_attribute('href')
                            img_tag = await item.query_selector('img')
                            image_url = await img_tag.get_attribute('src') if img_tag else ""
                            
                            rating_tag = await item.query_selector('span.r i.rating i')
                            rating_val = await rating_tag.inner_text() if rating_tag else "0.0"

                            clean_name = title.replace("مشاهدة", "").replace("مسلسل", "").replace("مترجم", "").strip()
                            year_match = re.search(r'(\d{4})', clean_name)
                            year = int(year_match.group(1)) if year_match else 2025

                            all_series.append({
                                "name": f"[EgiBest] {clean_name}",
                                "url": href,
                                "image_url": image_url,
                                "year": year,
                                "genre": "مسلسلات",
                                "rating": float(rating_val) if rating_val else 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except: continue
                    
                    print(f"✅ تم سحب {len(items)} مسلسل من صفحة {current_page}")
                    current_page += 1
                    
                except Exception as e:
                    print(f"❌ خطأ في صفحة {current_page}: {e}")
                    break

    finally:
        if all_series:
            # 1. إزالة التكرار بناءً على الرابط
            unique_series = list({s['url']: s for s in all_series}.values())
            total_count = len(unique_series)
            chunk_size = 10000 # تقسيم كل 10 آلاف في ملف
            
            print(f"📦 إجمالي المسلسلات المسحوبة: {total_count}. جاري التقسيم والحفظ...")

            # 2. تقسيم البيانات لحل مشكلة حجم الملف في GitHub
            for i in range(0, total_count, chunk_size):
                chunk = unique_series[i : i + chunk_size]
                part_num = (i // chunk_size) + 1
                filename = f"egibest_series_part{part_num}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=4)
                print(f"💾 تم حفظ الجزء {part_num} في ملف: {filename}")
        else:
            print("❌ لم يتم العثور على بيانات لحفظها.")
        
        if browser_instance:
            await browser_instance.close()

if __name__ == "__main__":
    # سيقوم الآن بسحب كافة الصفحات تلقائياً
    asyncio.run(scrape_egibest_series())