import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import os

async def scrape_laroza_movies(max_pages_per_category=None):
    all_movies = []
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    # الدومين الجديد بـ 2 'z'
    base_url = "https://larozza.xyz"
    
    movie_categories = [
        f"{base_url}/category.php?cat=arabic-movies33",
        f"{base_url}/category.php?cat=all_movies_13",
        f"{base_url}/category.php?cat=indian-movies9",
        f"{base_url}/category.php?cat=6-asian-movies",
        f"{base_url}/category.php?cat=anime-movies-7",
        f"{base_url}/category.php?cat=7-aflammdblgh",
        f"{base_url}/category.php?cat=8-aflam3isk",
        f"{base_url}/category.php?cat=masrh-5",
    ]

    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                viewport={"width": 1280, "height": 1000},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            )
            page = await context.new_page()

            # تعطيل الصور للسرعة
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            for cat_url in movie_categories:
                current_page = 1
                category_name = cat_url.split("=")[-1]
                print(f"📡 جاري سحب الفئة: {category_name}...")

                while True:
                    if max_pages_per_category is not None and current_page > max_pages_per_category:
                        break

                    try:
                        await page.goto(f"{cat_url}&page={current_page}", wait_until="domcontentloaded", timeout=90000)
                        
                        # انتظار بسيط لضمان تحميل الـ HTML
                        await asyncio.sleep(2)

                        # التعديل هنا: استخدام li.col-xs-6 بناءً على الـ HTML اللي بعته
                        items = await page.query_selector_all("li.col-xs-6")
                        
                        if not items:
                            print(f"🏁 نهاية الفئة {category_name} عند صفحة {current_page-1}")
                            break

                        for item in items:
                            try:
                                # استخراج العنوان والرابط من الـ a اللي جوه h3
                                link_tag = await item.query_selector("div.caption h3 a")
                                if not link_tag: continue
                                
                                title = await link_tag.get_attribute("title")
                                href = await link_tag.get_attribute("href")
                                
                                if not title or any(word in title.lower() for word in blacklist):
                                    continue

                                # استخراج الصورة
                                img_tag = await item.query_selector("img")
                                image_url = await img_tag.get_attribute("src") if img_tag else ""

                                clean_name = (
                                    title.replace("مشاهدة", "")
                                    .replace("فيلم", "")
                                    .replace("اون لاين", "")
                                    .replace("كامل", "")
                                    .replace("HD", "")
                                    .strip()
                                )
                                
                                year_match = re.search(r"(\d{4})", title)

                                all_movies.append({
                                    "name": f"[لاروزا] {clean_name}",
                                    "url": href if href.startswith("http") else f"{base_url}/{href}",
                                    "image_url": image_url if image_url.startswith("http") else f"{base_url}/{image_url}",
                                    "year": int(year_match.group(1)) if year_match else 2026,
                                    "genre": "أفلام",
                                    "rating": 0.0,
                                    "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                                })
                            except:
                                continue

                        print(f"✅ {category_name} - صفحة {current_page}: تم جمع {len(items)} عنصر.")
                        current_page += 1
                    except Exception as e:
                        print(f"⚠️ خطأ في صفحة {current_page}: {e}")
                        break

    except Exception as e:
        print(f"❌ خطأ في المحرك: {e}")
    finally:
        if browser_instance:
            await browser_instance.close()

        if all_movies:
            unique_movies = list({m["url"]: m for m in all_movies}.values())
            filename = "laroza_movies.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(unique_movies, f, ensure_ascii=False, indent=4)
            print(f"💾 تم حفظ {len(unique_movies)} فيلم في: {filename}")
        else:
            print("ℹ️ لم يتم العثور على بيانات.")

if __name__ == "__main__":
    # تشغيل صفحة واحدة للتجربة كما طلبت
    asyncio.run(scrape_laroza_movies())