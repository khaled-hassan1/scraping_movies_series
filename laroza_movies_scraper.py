import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_laroza_movies(max_pages_per_category=None): # يمكنك تغيير عدد الصفحات هنا
    all_movies = [] 
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

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for base_url in movie_categories:
            category_name = base_url.split('=')[-1]
            
            for current_page in range(1, max_pages_per_category + 1):
                # دمج رقم الصفحة مع رابط القسم
                url = f"{base_url}&page={current_page}"
                print(f"📡 سحب قسم [{category_name}] - صفحة {current_page}...")
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    # التمرير لضمان ظهور روابط الصور
                    for _ in range(3):
                        await page.mouse.wheel(0, 1500)
                        await asyncio.sleep(0.3)

                    await page.wait_for_selector('li.col-xs-6', timeout=10000)
                    items = await page.query_selector_all('li.col-xs-6')

                    if not items:
                        print(f"⏹ لا يوجد مزيد من الأفلام في صفحة {current_page}.")
                        break

                    for item in items:
                        try:
                            link_tag = await item.query_selector('h3 a')
                            if not link_tag: continue
                            
                            full_title = await link_tag.get_attribute('title')
                            href = await link_tag.get_attribute('href')
                            
                            if any(word in full_title.lower() for word in blacklist):
                                continue

                            img_tag = await item.query_selector('img.img-responsive')
                            image_url = ""
                            if img_tag:
                                image_url = await img_tag.get_attribute('data-src') or \
                                            await img_tag.get_attribute('data-lazy-src') or \
                                            await img_tag.get_attribute('data-original') or \
                                            await img_tag.get_attribute('src')

                            clean_name = full_title.replace("مشاهدة", "").replace("فيلم", "").replace("اون لاين", "").replace("لاروزا", "").strip()
                            year_match = re.search(r'(\d{4})', clean_name)
                            year = int(year_match.group(1)) if year_match else 2025
                            
                            all_movies.append({
                                "name": f"[لاروزا] {clean_name}",
                                "url": href if href.startswith('http') else f"https://laroza.makeup/{href}",
                                "image_url": image_url,
                                "year": year,
                                "genre": "أفلام",
                                "rating": 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except:
                            continue
                    
                except Exception as e:
                    print(f"⚠️ خطأ في {url}: {str(e)[:40]}")
                    break # الانتقال للقسم التالي عند حدوث خطأ أو انتهاء الصفحات

        await browser.close()
        
        if all_movies:
            # تنظيف التكرار
            unique_movies = {m['url']: m for m in all_movies}.values()
            with open('laroza_movies.json', 'w', encoding='utf-8') as f:
                json.dump(list(unique_movies), f, ensure_ascii=False, indent=4)
            print(f"✅ اكتمل! تم حفظ {len(unique_movies)} فيلم فريد.")

if __name__ == "__main__":
    # للاختبار نسحب صفحة واحدة من كل قسم، ارفع الرقم لجلب كل شيء
    asyncio.run(scrape_laroza_movies())