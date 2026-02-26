import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_mycima_series(max_pages=None):
    all_series = [] 
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    async with async_playwright() as p:
        # تشغيل المتصفح مع إعدادات إضافية لتجنب الحظر
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        # حيلة سحرية: منع تحميل الصور لتسريع العملية وتجنب الـ Timeout
        await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

        current_page = 1
        while current_page <= max_pages:
            url = f"https://my-cima.pro/categories-4cima.php?cat=mosalsalat-4Cima-6&page={current_page}&order=DESC"
            print(f"📡 جاري محاولة فتح صفحة {current_page}...")
            
            try:
                # تغيير wait_until إلى 'commit' يجعل السحب أسرع ولا ينتظر تحميل الإعلانات
                await page.goto(url, wait_until="commit", timeout=90000)
                
                # ننتظر ظهور أي عنصر من عناصر المسلسلات لمدة 10 ثواني
                await page.wait_for_selector('li.col-xs-6', timeout=15000)
                
                items = await page.query_selector_all('li.col-xs-6')
                if not items: break

                for item in items:
                    title_tag = await item.query_selector('h3 a')
                    if not title_tag: continue
                    
                    full_title = await title_tag.get_attribute('title')
                    if any(word in full_title.lower() for word in blacklist):
                        continue

                    href = await title_tag.get_attribute('href')
                    img_tag = await item.query_selector('img')
                    image_url = await img_tag.get_attribute('src')
                    
                    clean_name = full_title.replace("مشاهدة", "").replace("ماي سيما", "").strip()
                    year_match = re.search(r'(\d{4})', clean_name)
                    year = int(year_match.group(1)) if year_match else 2025
                    
                    all_series.append({
                        "name": f"[مسلسل] {clean_name}",
                        "url": href if href.startswith('http') else f"https://my-cima.pro/{href}",
                        "image_url": image_url,
                        "year": year,
                        "genre": "مسلسلات",
                        "rating": 0.0,
                        "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    })
                
                print(f"✅ تم سحب {len(all_series)} مسلسل حتى الآن.")
                current_page += 1
                await asyncio.sleep(2) # راحة للموقع

            except Exception as e:
                print(f"⚠️ واجهنا مشكلة في صفحة {current_page}: {str(e)[:100]}")
                break

        await browser.close()
        
        if all_series:
            with open('mycima_series.json', 'w', encoding='utf-8') as f:
                json.dump(all_series, f, ensure_ascii=False, indent=4)
            print(f"🏁 تم الحفظ بنجاح!")

if __name__ == "__main__":
    asyncio.run(scrape_mycima_series())