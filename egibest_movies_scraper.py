import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_egibest(max_pages=None):
    all_movies = [] 
    browser = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            current_page = 1
            while max_pages is None or current_page <= max_pages:
                url = f"https://egibest.live/category/movies/page/{current_page}/"
                print(f"📡 جاري سحب إيجي بست (صفحة {current_page})...")
                
                try:
                    response = await page.goto(url, wait_until="commit", timeout=60000)
                    if response.status == 404: break

                    items = await page.query_selector_all('div.item')
                    if not items: break

                    for item in items:
                        try:
                            title_tag = await item.query_selector('span.title')
                            title = await title_tag.inner_text()
                            if any(word in title.lower() for word in blacklist): continue

                            href = await (await item.query_selector('a')).get_attribute('href')
                            img_tag = await item.query_selector('img')
                            image_url = await img_tag.get_attribute('src')

                            clean_name = title.replace("مشاهدة", "").strip()
                            year_match = re.search(r'(\d{4})', clean_name)
                            year = int(year_match.group(1)) if year_match else 2026

                            all_movies.append({
                                "name": f"[EgiBest] {clean_name}",
                                "url": href, "image_url": image_url, "year": year,
                                "genre": "أفلام", "rating": 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except: continue
                    current_page += 1
                except: break
    finally:
        if all_movies:
            with open('egibest_movies.json', 'w', encoding='utf-8') as f:
                json.dump(all_movies, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(all_movies)} فيلم من إيجي بست.")
        if browser: await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_egibest())