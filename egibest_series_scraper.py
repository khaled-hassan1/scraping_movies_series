import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_egibest_series(max_pages=None):
    all_series = [] 
    # قائمة الكلمات المحظورة لضمان أمان المحتوى
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # حظر الصور لتسريع العملية وتقليل استهلاك البيانات في الـ Action
        await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

        current_page = 1
        while current_page <= max_pages:
            url = f"https://egibest.live/category/series/page/{current_page}/"
            print(f"📡 جاري سحب مسلسلات إيجي بست (صفحة {current_page})...")
            
            try:
                # الدخول للرابط والانتظار حتى بداية استلام البيانات
                await page.goto(url, wait_until="commit", timeout=60000)
                
                # انتظار ظهور بلوكات المسلسلات (نفس الـ selector الخاص بالأفلام)
                await page.wait_for_selector('a.postBlockCol', timeout=15000)
                items = await page.query_selector_all('a.postBlockCol')
                
                if not items: break

                for item in items:
                    try:
                        # 1. العنوان والرابط
                        title = await item.get_attribute('title')
                        if not title:
                            h3 = await item.query_selector('h3.title')
                            title = await h3.inner_text()
                        
                        # فلترة المحتوى فوراً
                        if any(word in title.lower() for word in blacklist):
                            continue

                        href = await item.get_attribute('href')
                        
                        # 2. صورة البوستر
                        img_tag = await item.query_selector('img')
                        image_url = await img_tag.get_attribute('src') if img_tag else ""
                        
                        # 3. التقييم (إن وجد)
                        rating_val = 0.0
                        rating_tag = await item.query_selector('i.rating i')
                        if rating_tag:
                            r_text = await rating_tag.inner_text()
                            rating_val = float(r_text) if r_text else 0.0

                        # 4. تنظيف الاسم واستخراج السنة
                        clean_name = title.replace("مشاهدة", "").replace("إيجي بست", "").replace("مسلسل", "").strip()
                        year_match = re.search(r'(\d{4})', clean_name)
                        year = int(year_match.group(1)) if year_match else 2025
                        
                        all_series.append({
                            "name": f"[مسلسل] {clean_name}",
                            "url": href,
                            "image_url": image_url,
                            "year": year,
                            "genre": "مسلسلات",
                            "rating": rating_val,
                            "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        })
                    except:
                        continue
                
                current_page += 1
            except Exception as e:
                print(f"⚠️ انتهت الصفحات أو حدث خطأ: {str(e)[:50]}")
                break

        await browser.close()
        
        if all_series:
            filename = 'egibest_series.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_series, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(all_series)} مسلسل من إيجي بست بنجاح.")

if __name__ == "__main__":
    # يمكنك زيادة عدد الصفحات هنا (مثلاً 5 صفحات)
    asyncio.run(scrape_egibest_series())