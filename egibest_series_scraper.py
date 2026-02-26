import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_egibest_series(max_pages=2):
    all_series = [] 
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            # تشغيل المتصفح مع إعدادات تخطي الحماية
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # تسريع السحب بمنع الصور
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            current_page = 1
            while current_page <= max_pages:
                # الرابط المباشر للمسلسلات
                url = f"https://egibest.live/series/page/{current_page}/"
                print(f"📡 جاري سحب مسلسلات إيجي بست (صفحة {current_page})...")
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(3) # وقت لضمان تحميل الـ JavaScript

                    # السيلكتور الجديد من ملف ع.txt
                    items = await page.query_selector_all('a.postBlockCol')
                    
                    if not items:
                        print(f"⚠️ لم يتم العثور على مسلسلات في صفحة {current_page}")
                        break

                    for item in items:
                        try:
                            # 1. العنوان من h3.title
                            title_tag = await item.query_selector('h3.title')
                            title = await title_tag.inner_text() if title_tag else ""
                            
                            if not title or any(word in title.lower() for word in blacklist):
                                continue

                            # 2. الرابط من الـ a نفسه
                            href = await item.get_attribute('href')

                            # 3. الصورة
                            img_tag = await item.query_selector('img')
                            image_url = await img_tag.get_attribute('src') if img_tag else ""

                            # 4. التقييم
                            rating_tag = await item.query_selector('span.r i.rating i')
                            rating_val = await rating_tag.inner_text() if rating_tag else "0.0"

                            # تنظيف الاسم
                            clean_name = title.replace("مشاهدة", "").replace("مسلسل", "").replace("مترجم", "").strip()
                            
                            # استخراج السنة
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
            # حذف التكرار
            unique_series = list({s['url']: s for s in all_series}.values())
            with open('egibest_series.json', 'w', encoding='utf-8') as f:
                json.dump(unique_series, f, ensure_ascii=False, indent=4)
            print(f"🏁 تم حفظ {len(unique_series)} مسلسل بنجاح.")
        else:
            print("❌ لم يتم العثور على أي مسلسلات.")
        
        if browser_instance:
            await browser_instance.close()

if __name__ == "__main__":
    # افتراضياً هسحب أول صفحتين للتجربة، تقدر تغير الرقم
    asyncio.run(scrape_egibest_series())