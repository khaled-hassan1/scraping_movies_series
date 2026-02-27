# import asyncio
# from playwright.async_api import async_playwright
# import json
# from datetime import datetime
# import re

# async def scrape_123movies_imdb(max_pages=None):
#     all_items = []
#     base_url = "https://ww8.123moviesfree.net/top-imdb/all/"
    
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
#         page = await context.new_page()
        
#         current_page = 1
#         while True:
#             if max_pages and current_page > max_pages: break
            
#             url = f"{base_url}?page={current_page}"
#             print(f"📡 سحب IMDb صفحة {current_page}...")
            
#             try:
#                 response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
#                 if response.status == 404: break

#                 items = await page.query_selector_all('div.col')
#                 if not items: break

#                 for item in items:
#                     try:
#                         title_tag = await item.query_selector('h2.card-title')
#                         title = await title_tag.inner_text()
#                         link_tag = await item.query_selector('a.poster')
#                         href = await link_tag.get_attribute('href')
#                         img_tag = await item.query_selector('img')
#                         image_url = await img_tag.get_attribute('data-src') or await img_tag.get_attribute('src')
                        
#                         all_items.append({
#                             "name": f"[IMDb] {title.strip()}",
#                             "url": href if href.startswith('http') else f"https://ww8.123moviesfree.net{href}",
#                             "image_url": image_url,
#                             "year": 2025, # المصدر غالباً لا يضع السنة في العناوين هنا
#                             "genre": "Top IMDb",
#                             "rating": 0.0,
#                             "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
#                         })
#                     except: continue
#                 current_page += 1
#             except: break

#         # حفظ البيانات بالتقسيم
#         if all_items:
#             chunk_size = 10000
#             for i in range(0, len(all_items), chunk_size):
#                 chunk = all_items[i : i + chunk_size]
#                 part = (i // chunk_size) + 1
#                 with open(f'imdb_movies_part{part}.json', 'w', encoding='utf-8') as f:
#                     json.dump(chunk, f, ensure_ascii=False, indent=4)
#         await browser.close()

# if __name__ == "__main__":
#     asyncio.run(scrape_123movies_imdb())