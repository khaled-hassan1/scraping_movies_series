import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_egibest(max_pages=2):
    all_movies = [] 
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            current_page = 1
            while current_page <= max_pages:
                # الرابط بناءً على بنية الموقع
                url = f"https://egibest.live/movies/page/{current_page}/"
                print(f"📡 جاري سحب إيجي بست (صفحة {current_page})...")
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(3) # انتظار بسيط للتأكد من تحميل العناصر

                    # السيلكتور الصحيح بناءً على ملف ع.txt اللي بعته
                    items = await page.query_selector_all('a.postBlockCol')
                    
                    if not items:
                        print(f"⚠️ لم يتم العثور على عناصر. جاري محاولة سيلكتور بديل...")
                        items = await page.query_selector_all('div#loadPost a')

                    for item in items:
                        try:
                            # 1. استخراج العنوان من h3.title
                            title_tag = await item.query_selector('h3.title')
                            title = await title_tag.inner_text() if title_tag else ""
                            
                            if not title or any(word in title.lower() for word in blacklist):
                                continue

                            # 2. استخراج الرابط
                            href = await item.get_attribute('href')

                            # 3. استخراج الصورة
                            img_tag = await item.query_selector('img')
                            image_url = await img_tag.get_attribute('src') if img_tag else ""

                            # 4. استخراج التقييم (لو موجود)
                            rating_tag = await item.query_selector('span.r i.rating i')
                            rating = await rating_tag.inner_text() if rating_tag else "0.0"

                            clean_name = title.replace("مشاهدة", "").replace("فيلم", "").replace("مترجم", "").strip()
                            year_match = re.search(r'(\d{4})', clean_name)
                            year = int(year_match.group(1)) if year_match else 2026

                            all_movies.append({
                                "name": f"[EgiBest] {clean_name}",
                                "url": href,
                                "image_url": image_url,
                                "year": year,
                                "genre": "أفلام",
                                "rating": float(rating) if rating else 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except: continue
                    
                    print(f"✅ تم سحب {len(items)} عنصر من صفحة {current_page}")
                    current_page += 1
                except Exception as e:
                    print(f"❌ توقف السحب عند صفحة {current_page}: {e}")
                    break
    finally:
        if all_movies:
            unique_movies = list({m['url']: m for m in all_movies}.values())
            with open('egibest_movies.json', 'w', encoding='utf-8') as f:
                json.dump(unique_movies, f, ensure_ascii=False, indent=4)
            print(f"🏁 انتهى! تم حفظ {len(unique_movies)} فيلم في egibest_movies.json")
        else:
            print("❌ فشل السحب: لم يتم العثور على أي بيانات. تأكد من أن الرابط movies متاح.")
        
        if browser_instance:
            await browser_instance.close()

if __name__ == "__main__":
    asyncio.run(scrape_egibest())