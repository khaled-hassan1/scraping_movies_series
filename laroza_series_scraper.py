import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_laroza_series(max_pages=None):
    all_series = [] 
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            page = await browser_instance.new_page()
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            current_page = 1
            while max_pages is None or current_page <= max_pages:
                url = f"https://laroza.makeup/moslslat4.php?page={current_page}"
                print(f"📡 جاري سحب مسلسلات لاروزا (صفحة {current_page})...")
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    items = await page.query_selector_all('li.col-xs-6')
                    if not items: break

                    for item in items:
                        try:
                            title_tag = await item.query_selector('h3 a')
                            title = await title_tag.inner_text()
                            if any(word in title.lower() for word in blacklist): continue

                            href = await title_tag.get_attribute('href')
                            img_tag = await item.query_selector('img')
                            image_url = await img_tag.get_attribute('src')

                            all_series.append({
                                "name": f"[لاروزا] {title.strip()}",
                                "url": f"https://laroza.makeup/{href}",
                                "image_url": image_url, "year": 2026,
                                "genre": "مسلسلات", "rating": 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except: continue
                    current_page += 1
                except: break
    finally:
        if all_series:
            with open('laroza_series.json', 'w', encoding='utf-8') as f:
                json.dump(all_series, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(all_series)} مسلسل من لاروزا.")
        if browser_instance: await browser_instance.close()

if __name__ == "__main__":
    asyncio.run(scrape_laroza_series())