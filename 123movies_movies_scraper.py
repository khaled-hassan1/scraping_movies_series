import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_123movies_direct(max_pages=None):
    all_movies = []
    # الرابط المباشر للمصدر اللي vumoo بيعرضه
    base_url = "https://ww8.123moviesfree.net/movie/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        current_page = 1
        while True:
            if max_pages is not None and current_page > max_pages:
                break
                
            url = f"{base_url}?page={current_page}"
            print(f"📡 سحب صفحة {current_page} من المصدر المباشر...")
            
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                if response.status == 404: break

                # انتظار بسيط لضمان تحميل العناصر
                await asyncio.sleep(2)

                # السيلكتورز بناءً على الكود اللي بعته (card h-100)
                items = await page.query_selector_all('div.col')
                if not items: break

                for item in items:
                    try:
                        # استخراج العنوان
                        title_tag = await item.query_selector('h2.card-title')
                        if not title_tag: continue
                        title = await title_tag.inner_text()

                        # استخراج الرابط
                        link_tag = await item.query_selector('a.poster')
                        href = await link_tag.get_attribute('href')

                        # استخراج الصورة (الموقع بيستخدم lazy loading)
                        img_tag = await item.query_selector('img')
                        image_url = ""
                        if img_tag:
                            image_url = await img_tag.get_attribute('data-src') or \
                                        await img_tag.get_attribute('src')

                        # استخراج السنة من العنوان إن وجدت
                        year_match = re.search(r'(\d{4})', title)
                        year = int(year_match.group(1)) if year_match else 2025

                        all_movies.append({
                            "name": f"[123Movies] {title.strip()}",
                            "url": href if href.startswith('http') else f"https://ww8.123moviesfree.net{href}",
                            "image_url": image_url,
                            "year": year,
                            "genre": "Movies",
                            "rating": 0.0,
                            "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        })
                    except: continue
                
                print(f"✅ تم جمع {len(items)} فيلم من صفحة {current_page}")
                current_page += 1
                
            except Exception as e:
                print(f"❌ خطأ في صفحة {current_page}: {e}")
                break

        if all_movies:
            # إزالة التكرار
            unique_movies = list({m['url']: m for m in all_movies}.values())
            # تقسيم وحفظ (Chunks) لضمان عدم تخطي مساحة GitHub
            chunk_size = 10000
            for i in range(0, len(unique_movies), chunk_size):
                chunk = unique_movies[i : i + chunk_size]
                part = (i // chunk_size) + 1
                filename = f"123movies_part{part}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=4)
                print(f"💾 تم حفظ {len(chunk)} فيلم في {filename}")

        await browser.close()

if __name__ == "__main__":
    # جرب تسحب أول 5 صفحات كمثال، أو None لكل الموقع
    asyncio.run(scrape_123movies_direct())