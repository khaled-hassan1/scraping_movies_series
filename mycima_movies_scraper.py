import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_mycima_safe(max_pages=1):
    all_movies = [] 
    # كلمات الحظر
    blacklist = ["+18", "للكبار فقط", "افلام جنس", "جنسي", "sex", "adult", "18+"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        current_page = 1
        while current_page <= max_pages:
            url = f"https://my-cima.pro/topvideos-mycima.php?&page={current_page}"
            print(f"📡 جاري سحب صفحة {current_page} (فلترة المحتوى نشطة)...")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                items = await page.query_selector_all('li.col-xs-6')
                
                if not items: break

                for item in items:
                    title_tag = await item.query_selector('h3 a')
                    full_title = await title_tag.get_attribute('title')
                    
                    # الفلترة الذكية
                    if any(word in full_title.lower() for word in blacklist):
                        continue # تجاهل الفيلم
                    
                    # استكمال البيانات العادية
                    clean_name = full_title.replace("مشاهدة", "").replace("ماي سيما", "").strip()
                    href = await title_tag.get_attribute('href')
                    img_tag = await item.query_selector('img')
                    image_url = await img_tag.get_attribute('src')
                    
                    year_match = re.search(r'(\d{4})', clean_name)
                    year = int(year_match.group(1)) if year_match else 2025

                    all_movies.append({
                        "name": f"[ماي سيما] {clean_name}",
                        "url": href,
                        "image_url": image_url,
                        "year": year,
                        "genre": "أفلام",
                        "rating": 0.0,
                        "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    })
                
                current_page += 1
            except:
                break
                
        await browser.close()
        
        # حفظ الملف
        with open('mycima_movies.json', 'w', encoding='utf-8') as f:
            json.dump(all_movies, f, ensure_ascii=False, indent=4)
        print(f"✅ تم الانتهاء. الإجمالي بعد الفلترة: {len(all_movies)} فيلم.")

if __name__ == "__main__":
    asyncio.run(scrape_mycima_safe())