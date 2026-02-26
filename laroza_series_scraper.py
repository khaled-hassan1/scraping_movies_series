import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_laroza_series(max_pages=None):
    all_series = [] 
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # ملاحظة: أزلنا حظر الصور هنا لضمان عمل الـ Lazy Load برمجياً
        # لكن سنمنع تحميل الصور فعلياً لتوفير البيانات

        current_page = 1
        while current_page <= max_pages:
            url = f"https://laroza.makeup/moslslat4.php?page={current_page}"
            print(f"📡 جاري سحب صفحة {current_page} مع تفعيل الصور...")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # --- خطوة سحرية: التمرير لأسفل لتفعيل كل الروابط ---
                for i in range(5): # تمرير تدريجي
                    await page.mouse.wheel(0, 2000)
                    await asyncio.sleep(0.5)
                
                await page.wait_for_selector('li.col-xs-6', timeout=15000)
                items = await page.query_selector_all('li.col-xs-6')
                
                if not items: break

                for item in items:
                    try:
                        link_tag = await item.query_selector('h3 a')
                        if not link_tag: continue
                        
                        full_title = await link_tag.get_attribute('title')
                        href = await link_tag.get_attribute('href')
                        
                        if any(word in full_title.lower() for word in blacklist):
                            continue

                        # جلب الصورة مع فحص جميع الاحتمالات
                        img_tag = await item.query_selector('img.img-responsive')
                        image_url = ""
                        if img_tag:
                            # جرب كل السمات الممكنة التي يضع فيها الموقع روابطه
                            image_url = await img_tag.get_attribute('data-src') or \
                                        await img_tag.get_attribute('data-lazy-src') or \
                                        await img_tag.get_attribute('src')
                            
                            # إذا كان الرابط لا يزال Base64 أو فارغاً، خذ الرابط من الـ "data-original" إن وجد
                            if not image_url or image_url.startswith('data:'):
                                image_url = await img_tag.get_attribute('data-original') or ""

                        clean_name = full_title.replace("مشاهدة", "").replace("لاروزا", "").strip()
                        year_match = re.search(r'(\d{4})', clean_name)
                        year = int(year_match.group(1)) if year_match else 2025
                        
                        all_series.append({
                            "name": f"[لاروزا] {clean_name}",
                            "url": href if href.startswith('http') else f"https://laroza.makeup/{href}",
                            "image_url": image_url,
                            "year": year,
                            "genre": "مسلسلات",
                            "rating": 0.0,
                            "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        })
                    except:
                        continue
                
                current_page += 1
            except Exception as e:
                print(f"⚠️ خطأ: {str(e)[:50]}")
                break

        await browser.close()
        
        if all_series:
            with open('laroza_series.json', 'w', encoding='utf-8') as f:
                json.dump(all_series, f, ensure_ascii=False, indent=4)
            print(f"✅ تم سحب {len(all_series)} بنجاح مع روابط الصور.")

if __name__ == "__main__":
    asyncio.run(scrape_laroza_series())