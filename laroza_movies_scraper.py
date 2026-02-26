import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

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
            
            # منع الصور الثقيلة لتسريع العملية (اختياري)
            # await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            for base_url in movie_categories:
                category_name = base_url.split('=')[-1]
                current_page = 1
                
                while True:
                    # التحقق من سقف الصفحات لكل قسم
                    if max_pages_per_category is not None and current_page > max_pages_per_category:
                        break

                    url = f"{base_url}&page={current_page}"
                    print(f"📡 سحب قسم [{category_name}] - صفحة {current_page}...")
                    
                    try:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                        
                        if response and response.status == 404:
                            break

                        # تمرير بسيط لتفعيل الـ Lazy Load للصور
                        await page.evaluate("window.scrollBy(0, 1000)")
                        await asyncio.sleep(0.5)

                        await page.wait_for_selector('li.col-xs-6', timeout=10000)
                        items = await page.query_selector_all('li.col-xs-6')

                        if not items:
                            break

                        for item in items:
                            try:
                                link_tag = await item.query_selector('h3 a')
                                if not link_tag: continue
                                
                                full_title = await link_tag.get_attribute('title')
                                if not full_title:
                                    full_title = await link_tag.inner_text()
                                
                                # فلتر الأمان
                                if any(word in full_title.lower() for word in blacklist):
                                    continue

                                href = await link_tag.get_attribute('href')
                                img_tag = await item.query_selector('img')
                                image_url = ""
                                if img_tag:
                                    image_url = await img_tag.get_attribute('data-src') or \
                                                await img_tag.get_attribute('data-original') or \
                                                await img_tag.get_attribute('src')

                                clean_name = full_title.replace("مشاهدة", "").replace("فيلم", "").replace("اون لاين", "").replace("لاروزا", "").strip()
                                year_match = re.search(r'(\d{4})', clean_name)
                                
                                all_movies.append({
                                    "name": f"[لاروزا] {clean_name}",
                                    "url": href if href.startswith('http') else f"https://laroza.makeup/{href}",
                                    "image_url": image_url,
                                    "year": int(year_match.group(1)) if year_match else 2025,
                                    "genre": "أفلام",
                                    "rating": 0.0,
                                    "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                                })
                            except:
                                continue
                        
                        current_page += 1
                        
                    except Exception as e:
                        print(f"⚠️ انتهى القسم أو حدث خطأ: {str(e)[:40]}")
                        break 

    except asyncio.CancelledError:
        print("\n⚠️ تم إيقاف السحب يدوياً.. جاري حفظ البيانات المجمعة...")
    except Exception as e:
        print(f"\n❌ حدث خطأ غير متوقع: {e}")
    
    finally:
        if all_movies:
            # تنظيف التكرار الناتج عن وجود الفيلم في أكثر من قسم
            unique_movies = list({m['url']: m for m in all_movies}.values())
            with open('laroza_movies.json', 'w', encoding='utf-8') as f:
                json.dump(unique_movies, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(unique_movies)} فيلم فريد من لاروزا.")
        else:
            print("ℹ️ لم يتم جمع أي بيانات.")
            
        if browser_instance:
            await browser_instance.close()

if __name__ == "__main__":
    try:
        # لسحب كل شيء اتركها فارغة، أو حدد رقماً للصفحات لكل قسم
        asyncio.run(scrape_laroza_movies(max_pages_per_category=None))
    except KeyboardInterrupt:
        pass