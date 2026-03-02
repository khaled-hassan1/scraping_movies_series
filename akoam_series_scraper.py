import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_akoam_series(max_pages=None):
    all_series = [] 
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
                    
                # رابط قسم المسلسلات
                url = f"https://ak.sv/series?page={current_page}"
                print(f"📡 جاري سحب صفحة المسلسلات {current_page} من أكوام...")
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    if response.status == 404: break

                    await asyncio.sleep(1) # وقت مستقطع للتحميل

                    # السليكتور من ملف الـ HTML اللي بعته هو .entry-box-1
                    items = await page.query_selector_all('.entry-box-1')
                    if not items: break

                    for item in items:
                        try:
                            # 1. الرابط والعنوان
                            link_tag = await item.query_selector('.entry-image a')
                            href = await link_tag.get_attribute('href')
                            
                            img_tag = await item.query_selector('.entry-image img')
                            raw_name = await img_tag.get_attribute('alt')
                            
                            # 2. الصورة
                            image_url = await img_tag.get_attribute('data-src') or await img_tag.get_attribute('src')
                            
                            # 3. استخراج السنة من العنوان (مثال: "مسلسل خريف عمر 2023" -> 2023)
                            year_match = re.search(r'(19|20)\d{2}', raw_name)
                            year = int(year_match.group()) if year_match else 2024
                            
                            # 4. التقييم والجودة (أكوام بيحط الجودة زي WEB-DL في كلاس quality)
                            rating_tag = await item.query_selector('.label.rating')
                            rating = await rating_tag.inner_text() if rating_tag else "0.0"
                            
                            quality_tag = await item.query_selector('.label.quality')
                            quality = await quality_tag.inner_text() if quality_tag else "مسلسل"

                            all_series.append({
                                "name": f"[أكوام] {raw_name.strip()}",
                                "url": href if href.startswith('http') else f"https://ak.sv{href}",
                                "image_url": image_url,
                                "year": year,
                                "genre": f"مسلسلات, {quality.strip()}",
                                "rating": float(rating.strip()) if rating.strip().replace('.','').isdigit() else 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except: continue
                    
                    current_page += 1
                except: break

    finally:
        if browser_instance: await browser_instance.close()

        if all_series:
            # حذف التكرار وحفظ البيانات
            unique_data = list({m['url']: m for m in all_series}.values())
            
            # التقسيم لملفات صغيرة (Chunks)
            chunk_size = 5000
            for i in range(0, len(unique_data), chunk_size):
                chunk = unique_data[i : i + chunk_size]
                part = (i // chunk_size) + 1
                filename = f'akoam_series_part{part}.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=2)
                print(f"✅ تم حفظ {len(chunk)} مسلسل في {filename}")
        else:
            print("❌ فشل في جمع بيانات المسلسلات.")

    return all_series

if __name__ == "__main__":
    asyncio.run(scrape_akoam_series())
