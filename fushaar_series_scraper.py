import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_fushaar_series(max_pages=None):
    all_series = [] 
    # فلتر الأمان
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # تسريع العملية بمنع الصور
        await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

        current_page = 1
        while current_page <= max_pages:
            url = f"https://fushaar.forum/category.php?cat=arabic-series&page={current_page}"
            print(f"📡 جاري سحب مسلسلات فشار العربية (صفحة {current_page})...")
            
            try:
                await page.goto(url, wait_until="commit", timeout=60000)
                
                # انتظار تحميل العناصر
                await page.wait_for_selector('li.col-xs-6', timeout=15000)
                items = await page.query_selector_all('li.col-xs-6')
                
                if not items: break

                for item in items:
                    try:
                        title_tag = await item.query_selector('h3 a')
                        full_title = await title_tag.get_attribute('title') or await title_tag.inner_text()
                        
                        # فلتر الأمان
                        if any(word in full_title.lower() for word in blacklist):
                            continue

                        href = await title_tag.get_attribute('href')
                        img_tag = await item.query_selector('img')
                        image_url = await img_tag.get_attribute('src')
                        
                        # تنظيف الاسم واستخراج السنة
                        clean_name = full_title.replace("مشاهدة", "").replace("مسلسل", "").replace("فشار", "").strip()
                        year_match = re.search(r'(\d{4})', clean_name)
                        year = int(year_match.group(1)) if year_match else 2025
                        
                        all_series.append({
                            "name": f"[مسلسل عربي] {clean_name}",
                            "url": href if href.startswith('http') else f"https://fushaar.forum/{href}",
                            "image_url": image_url,
                            "year": year,
                            "genre": "مسلسلات عربية",
                            "rating": 0.0,
                            "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        })
                    except:
                        continue
                
                current_page += 1
            except Exception as e:
                print(f"⚠️ توقف السحب: {str(e)[:50]}")
                break

        await browser.close()
        
        if all_series:
            with open('fushaar_series.json', 'w', encoding='utf-8') as f:
                json.dump(all_series, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(all_series)} مسلسل عربي من فشار.")

if __name__ == "__main__":
    asyncio.run(scrape_fushaar_series())