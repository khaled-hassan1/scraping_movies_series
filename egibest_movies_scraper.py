import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_egibest(max_pages=None):
    all_movies = [] 
    # فلتر الأمان
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # تسريع العملية بمنع الصور الثقيلة
        await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

        current_page = 1
        while current_page <= max_pages:
            url = f"https://egibest.live/category/movies/page/{current_page}/"
            print(f"📡 جاري سحب إيجي بست (صفحة {current_page})...")
            
            try:
                # نستخدم wait_until="commit" للسرعة
                await page.goto(url, wait_until="commit", timeout=60000)
                
                # انتظار ظهور بلوكات الأفلام بناءً على الكود اللي بعته
                await page.wait_for_selector('a.postBlockCol', timeout=15000)
                items = await page.query_selector_all('a.postBlockCol')
                
                if not items: break

                for item in items:
                    try:
                        # 1. العنوان (موجود في التايتل أو h3)
                        title = await item.get_attribute('title')
                        if not title:
                            h3 = await item.query_selector('h3.title')
                            title = await h3.inner_text()
                        
                        # فلتر الأمان
                        if any(word in title.lower() for word in blacklist):
                            continue

                        # 2. الرابط
                        href = await item.get_attribute('href')
                        
                        # 3. الصورة (نبحث عن الـ src داخل الـ img)
                        img_tag = await item.query_selector('img')
                        image_url = await img_tag.get_attribute('src') if img_tag else ""
                        
                        # 4. التقييم (موجود داخل i.rating i)
                        rating_val = 0.0
                        rating_tag = await item.query_selector('i.rating i')
                        if rating_tag:
                            r_text = await rating_tag.inner_text()
                            rating_val = float(r_text) if r_text else 0.0

                        # 5. تنظيف الاسم واستخراج السنة
                        clean_name = title.replace("مشاهدة", "").replace("إيجي بست", "").replace("مترجم اونلاين", "").strip()
                        year_match = re.search(r'(\d{4})', clean_name)
                        year = int(year_match.group(1)) if year_match else 2025
                        
                        all_movies.append({
                            "name": f"[EgiBest] {clean_name}",
                            "url": href,
                            "image_url": image_url,
                            "year": year,
                            "genre": "أفلام",
                            "rating": rating_val,
                            "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        })
                    except Exception as e:
                        continue
                
                current_page += 1
            except Exception as e:
                print(f"⚠️ توقف السحب أو اكتملت الصفحات.")
                break

        await browser.close()
        
        if all_movies:
            with open('egibest_movies.json', 'w', encoding='utf-8') as f:
                json.dump(all_movies, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(all_movies)} فيلم من إيجي بست.")

if __name__ == "__main__":
    asyncio.run(scrape_egibest())