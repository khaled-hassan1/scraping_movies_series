import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import os

async def scrape_123movies_series(max_pages=None):
    all_series = []
    # الرابط المباشر لقسم المسلسلات
    base_url = "https://ww8.123moviesfree.net/tv-series/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # منع الصور لتسريع العملية
        await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())
        
        current_page = 1
        while True:
            if max_pages is not None and current_page > max_pages:
                break
                
            url = f"{base_url}?page={current_page}"
            print(f"📡 سحب مسلسلات صفحة {current_page} من المصدر المباشر...")
            
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                if response.status == 404: break

                await asyncio.sleep(2) # انتظار بسيط لتحميل العناصر

                # السيلكتورز بناءً على بنية 123Movies
                items = await page.query_selector_all('div.col')
                if not items: break

                for item in items:
                    try:
                        # 1. استخراج العنوان
                        title_tag = await item.query_selector('h2.card-title')
                        if not title_tag: continue
                        title = await title_tag.inner_text()

                        # 2. استخراج الرابط
                        link_tag = await item.query_selector('a.poster')
                        href = await link_tag.get_attribute('href')

                        # 3. استخراج الصورة
                        img_tag = await item.query_selector('img')
                        image_url = ""
                        if img_tag:
                            image_url = await img_tag.get_attribute('data-src') or \
                                        await img_tag.get_attribute('src')

                        # 4. استخراج السنة من العنوان إن وجدت
                        year_match = re.search(r'(\d{4})', title)
                        year = int(year_match.group(1)) if year_match else 2025

                        all_series.append({
                            "name": f"[123Movies] {title.strip()}",
                            "url": href if href.startswith('http') else f"https://ww8.123moviesfree.net{href}",
                            "image_url": image_url,
                            "year": year,
                            "genre": "TV Series",
                            "rating": 0.0,
                            "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        })
                    except: continue
                
                print(f"✅ تم جمع {len(items)} مسلسل من صفحة {current_page}")
                current_page += 1
                
            except Exception as e:
                print(f"❌ خطأ في صفحة {current_page}: {e}")
                break

        # حفظ البيانات مع التقسيم (Chunks) لتجنب مشاكل GitHub
        if all_series:
            unique_series = list({s['url']: s for s in all_series}.values())
            total_count = len(unique_series)
            chunk_size = 10000 
            
            print(f"📦 إجمالي المسلسلات: {total_count}. جاري الحفظ...")

            for i in range(0, total_count, chunk_size):
                chunk = unique_series[i : i + chunk_size]
                part_num = (i // chunk_size) + 1
                filename = f"123movies_series_part{part_num}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=4)
                print(f"💾 تم حفظ {filename}")
        else:
            print("❌ لم يتم العثور على أي مسلسلات.")

        await browser.close()

if __name__ == "__main__":
    # اتركه None لسحب كل المسلسلات، أو حدد رقم للتجربة
    asyncio.run(scrape_123movies_series())