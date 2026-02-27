import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import os

async def scrape_123movies_direct(max_pages=None):
    all_movies = []
    browser_instance = None
    base_url = "https://ww8.123moviesfree.net/movie/"
    
    try:
        async with async_playwright() as p:
            # 1. تشغيل المتصفح مع معايير الأداء العالي
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # 2. منع تحميل الصور لتوفير الوقت والـ RAM (تحسين أداء)
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())
            
            current_page = 1
            while True:
                if max_pages is not None and current_page > max_pages:
                    break
                    
                url = f"{base_url}?page={current_page}"
                print(f"📡 سحب صفحة {current_page} من 123Movies...")
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    if response.status == 404: 
                        print(f"🏁 تم الوصول لنهاية الصفحات عند {current_page - 1}")
                        break

                    # انتظار بسيط للتأكد من استقرار الـ DOM
                    await asyncio.sleep(2)

                    items = await page.query_selector_all('div.col')
                    if not items: break

                    for item in items:
                        try:
                            title_tag = await item.query_selector('h2.card-title')
                            if not title_tag: continue
                            title = await title_tag.inner_text()

                            link_tag = await item.query_selector('a.poster')
                            href = await link_tag.get_attribute('href')

                            img_tag = await item.query_selector('img')
                            image_url = ""
                            if img_tag:
                                image_url = await img_tag.get_attribute('data-src') or \
                                            await img_tag.get_attribute('src')

                            year_match = re.search(r'(\d{4})', title)
                            year = int(year_match.group(1)) if year_match else 2026

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
                    
                    print(f"✅ صفحة {current_page}: تم جمع {len(items)} عنصر.")
                    current_page += 1
                    
                except Exception as e:
                    print(f"⚠️ خطأ في صفحة {current_page}: {e}")
                    break

    except Exception as e:
        print(f"❌ خطأ غير متوقع في المحرك الأساسي: {e}")

    finally:
        # --- التحسين رقم 2: قتل العمليات المعلقة ---
        if browser_instance:
            await browser_instance.close()
            print("🔒 تم إغلاق المتصفح وتنظيف الرام.")

        # --- الحفظ بنظام الـ Chunks ---
        if all_movies:
            unique_movies = list({m['url']: m for m in all_movies}.values())
            chunk_size = 10000
            for i in range(0, len(unique_movies), chunk_size):
                chunk = unique_movies[i : i + chunk_size]
                part = (i // chunk_size) + 1
                filename = f"123movies_part{part}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=4)
                print(f"💾 تم حفظ {filename}")
        else:
            print("❌ لم يتم العثور على بيانات.")

if __name__ == "__main__":
    # اتركه بدون باراميتر لسحب كل شيء (None)
    asyncio.run(scrape_123movies_direct())