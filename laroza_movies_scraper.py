import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_laroza_movies(max_pages_per_category=None):
    all_movies = [] 
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    movie_categories = [
        "https://laroza.makeup/category.php?cat=all_movies_13",
        "https://laroza.makeup/category.php?cat=arabic-movies33",
        "https://laroza.makeup/category.php?cat=indian-movies9",
        "https://laroza.makeup/category.php?cat=6-asian-movies",
        "https://laroza.makeup/category.php?cat=anime-movies-7",
        "https://laroza.makeup/category.php?cat=7-aflammdblgh",
        "https://laroza.makeup/category.php?cat=8-aflam3isk",
        "https://laroza.makeup/category.php?cat=masrh-5"
    ]

    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            page = await browser_instance.new_page()
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            # حل مشكلة الـ range مع None
            limit = max_pages_per_category if max_pages_per_category is not None else 100

            for base_url in movie_categories:
                for current_page in range(1, limit + 1):
                    url = f"{base_url}&page={current_page}"
                    print(f"📡 جاري سحب لاروزا أفلام (صفحة {current_page})...")
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

                                all_movies.append({
                                    "name": f"[لاروزا] {title.strip()}",
                                    "url": f"https://laroza.makeup/{href}",
                                    "image_url": image_url, "year": 2026,
                                    "genre": "أفلام", "rating": 0.0,
                                    "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                                })
                            except: continue
                    except: break
    finally:
        if all_movies:
            unique_movies = list({m['url']: m for m in all_movies}.values())
            with open('laroza_movies.json', 'w', encoding='utf-8') as f:
                json.dump(unique_movies, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(unique_movies)} فيلم من لاروزا.")
        if browser_instance: await browser_instance.close()

if __name__ == "__main__":
    asyncio.run(scrape_laroza_movies())