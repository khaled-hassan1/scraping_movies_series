import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_fushaar(max_pages=None):
    all_media = [] 
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            page = await browser_instance.new_page()
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            current_page = 1
            while max_pages is None or current_page <= max_pages:
                url = f"https://fushaar.forum/topvideos.php?&page={current_page}"
                print(f"📡 جاري سحب موقع فشار (صفحة {current_page})...")
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    if response and response.status == 404: break

                    items = await page.query_selector_all('li.col-xs-6')
                    if not items: break

                    for item in items:
                        try:
                            title_tag = await item.query_selector('h3 a')
                            full_title = await title_tag.get_attribute('title')
                            if any(word in full_title.lower() for word in blacklist): continue

                            href = await title_tag.get_attribute('href')
                            img_tag = await item.query_selector('img')
                            image_url = await img_tag.get_attribute('src')
                            
                            year_match = re.search(r'(\d{4})', full_title)
                            year = int(year_match.group(1)) if year_match else 2026

                            all_media.append({
                                "name": f"[فشار] {full_title}",
                                "url": href, "image_url": image_url, "year": year,
                                "genre": "أفلام", "rating": 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except: continue
                    current_page += 1
                except: break
    finally:
        if all_media:
            with open('fushaar_movies.json', 'w', encoding='utf-8') as f:
                json.dump(all_media, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(all_media)} فيلم من فشار.")
        if browser_instance: await browser_instance.close()

if __name__ == "__main__":
    asyncio.run(scrape_fushaar())