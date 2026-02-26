import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import os

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
            context = await browser_instance.new_context(
                viewport={'width': 1280, 'height': 1000},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            for cat_url in movie_categories:
                current_page = 1
                print(f"📡 جاري سحب الفئة: {cat_url.split('=')[-1]}...")
                
                while True:
                    if max_pages_per_category is not None and current_page > max_pages_per_category:
                        break
                    
                    try:
                        await page.goto(f"{cat_url}&page={current_page}", wait_until="commit", timeout=60000)
                        items = await page.query_selector_all('div.boxItem')
                        if not items: break

                        for item in items:
                            try:
                                title_tag = await item.query_selector('h3')
                                title = await title_tag.inner_text() if title_tag else ""
                                
                                if any(word in title.lower() for word in blacklist): continue
                                
                                clean_name = title.replace("مشاهدة", "").replace("فيلم", "").replace("اون لاين", "").strip()
                                link_tag = await item.query_selector('a')
                                href = await link_tag.get_attribute('href')
                                img_tag = await item.query_selector('img')
                                image_url = await img_tag.get_attribute('src')
                                
                                year_match = re.search(r'(\d{4})', clean_name)
                                
                                all_movies.append({
                                    "name": f"[لاروزا] {clean_name}",
                                    "url": href if href.startswith('http') else f"https://laroza.makeup/{href}",
                                    "image_url": image_url,
                                    "year": int(year_match.group(1)) if year_match else 2026,
                                    "genre": "أفلام",
                                    "rating": 0.0,
                                    "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                                })
                            except: continue
                        current_page += 1
                    except: break

    finally:
        if all_movies:
            # 1. إزالة التكرار
            unique_movies = list({m['url']: m for m in all_movies}.values())
            total_count = len(unique_movies)
            chunk_size = 10000 # العدد المطلوب في كل ملف
            
            print(f"📦 تم تجميع {total_count} فيلم. جاري التقسيم...")

            # 2. تقسيم القائمة إلى أجزاء وحفظ كل جزء في ملف
            for i in range(0, total_count, chunk_size):
                chunk = unique_movies[i : i + chunk_size]
                part_number = (i // chunk_size) + 1
                filename = f"laroza_movies_part{part_number}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=4)
                print(f"✅ تم حفظ {len(chunk)} فيلم في {filename}")
        
        if browser_instance:
            await browser_instance.close()

if __name__ == "__main__":
    asyncio.run(scrape_laroza_movies())