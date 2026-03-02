import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import os

async def scrape_akoam(max_pages=10): # حددت 10 صفحات للتجربة
    all_movies = [] 
    browser_instance = None 
    
    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                viewport={'width': 1280, 'height': 1000},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            current_page = 1
            while True:
                if max_pages is not None and current_page > max_pages:
                    break
                    
                url = f"https://ak.sv/movies?page={current_page}"
                print(f"📡 جاري سحب الصفحة {current_page} من أكوام...")
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    if response.status == 404:
                        break

                    # الانتظار قليلاً لضمان تحميل الصور
                    await asyncio.sleep(1) 

                    # السليكتور الصحيح لبوكس الفيلم في أكوام هو entry-box-1 أو col-lg-auto
                    items = await page.query_selector_all('.entry-box-1')
                    if not items: 
                        print("━ لم يتم العثور على عناصر، قد يكون السليكتور تغير.")
                        break

                    for item in items:
                        try:
                            # 1. جلب الرابط والعنوان
                            link_tag = await item.query_selector('.entry-image a')
                            href = await link_tag.get_attribute('href')
                            
                            img_tag = await item.query_selector('.entry-image img')
                            name = await img_tag.get_attribute('alt') # العنوان غالباً موجود في alt الصورة
                            
                            # 2. جلب الصورة (معالجة الـ Lazy Load)
                            image_url = await img_tag.get_attribute('data-src') or await img_tag.get_attribute('src')
                            
                            # 3. جلب التقييم
                            rating_tag = await item.query_selector('.label.rating')
                            rating_text = await rating_tag.inner_text() if rating_tag else "0.0"
                            
                            # 4. جلب الجودة (أكوام يضع الجودة بدلاً من السنة أحياناً في الفهرس)
                            quality_tag = await item.query_selector('.label.quality')
                            quality = await quality_tag.inner_text() if quality_tag else ""

                            all_movies.append({
                                "name": f"[أكوام] {name.strip()}" if name else "بدون عنوان",
                                "url": href if href.startswith('http') else f"https://ak.sv{href}",
                                "image_url": image_url,
                                "year": 2024, # أكوام لا يضع السنة دائماً في الصفحة الرئيسية للمسلسلات/الأفلام
                                "genre": quality.strip() or "أفلام",
                                "rating": rating_text.replace(" ", "").strip(),
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except Exception as e: 
                            continue
                    
                    current_page += 1
                except Exception as e:
                    print(f"⚠️ خطأ في الصفحة {current_page}: {e}")
                    break

    finally:
        if browser_instance:
            await browser_instance.close()

        # الحفظ والتقسيم
        if all_movies:
            # إزالة التكرار بناءً على الرابط
            unique_movies = list({m['url']: m for m in all_movies}.values())
            
            # حفظ في ملفات مقسمة (Chunks)
            chunk_size = 5000
            for i in range(0, len(unique_movies), chunk_size):
                chunk = unique_movies[i : i + chunk_size]
                part = (i // chunk_size) + 1
                filename = f'akoam_part{part}.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=2)
                print(f"✅ تم حفظ الجزء {part} بنجاح ({len(chunk)} عنصر)")
        else:
            print("❌ لم يتم جمع أي بيانات.")

    return all_movies

if __name__ == "__main__":
    asyncio.run(scrape_akoam())
