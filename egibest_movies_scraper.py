import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

# تغيير القيمة الافتراضية إلى None
async def scrape_egibest(max_pages=None):
    all_movies = [] 
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            current_page = 1
            while True:
                # شرط التوقف: لو وصلنا للحد المطلوب (لو max_pages مش None)
                if max_pages is not None and current_page > max_pages:
                    break

                url = f"https://egibest.live/movies/page/{current_page}/"
                print(f"📡 جاري سحب إيجي بست (صفحة {current_page})...")
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    # لو الموقع رجع 404 أو الصفحة مش موجودة يبقى خلصنا
                    if response.status == 404:
                        print(f"🏁 وصلنا لنهاية الصفحات عند الصفحة {current_page}")
                        break

                    await asyncio.sleep(2) # انتظار بسيط

                    items = await page.query_selector_all('a.postBlockCol')
                    
                    # لو الصفحة اشتغلت بس مفيهاش أفلام يبقى السحب خلص
                    if not items:
                        print(f"🛑 لا يوجد المزيد من العناصر. توقف السحب عند صفحة {current_page}")
                        break

                    for item in items:
                        try:
                            title_tag = await item.query_selector('h3.title')
                            title = await title_tag.inner_text() if title_tag else ""
                            
                            if not title or any(word in title.lower() for word in blacklist):
                                continue

                            href = await item.get_attribute('href')
                            img_tag = await item.query_selector('img')
                            image_url = await img_tag.get_attribute('src') if img_tag else ""
                            
                            rating_tag = await item.query_selector('span.r i.rating i')
                            rating = await rating_tag.inner_text() if rating_tag else "0.0"

                            clean_name = title.replace("مشاهدة", "").replace("فيلم", "").replace("مترجم", "").strip()
                            year_match = re.search(r'(\d{4})', clean_name)
                            year = int(year_match.group(1)) if year_match else 2026

                            all_movies.append({
                                "name": f"[EgiBest] {clean_name}",
                                "url": href,
                                "image_url": image_url,
                                "year": year,
                                "genre": "أفلام",
                                "rating": float(rating) if rating else 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except: continue
                    
                    print(f"✅ تم سحب {len(items)} عنصر من صفحة {current_page}")
                    current_page += 1
                    
                except Exception as e:
                    print(f"❌ حدث خطأ أو توقف الاتصال عند صفحة {current_page}: {e}")
                    break
    finally:
        if all_movies:
            unique_movies = list({m['url']: m for m in all_movies}.values())
            # تنبيه: بما إنك هتسحب "كله"، الملف ممكن يكون كبير، جرب تقسمه زي ما عملنا في لاروزا لو زاد عن 50 ميجا
            with open('egibest_movies.json', 'w', encoding='utf-8') as f:
                json.dump(unique_movies, f, ensure_ascii=False, indent=4)
            print(f"🏁 انتهى! تم حفظ {len(unique_movies)} فيلم في egibest_movies.json")
        
        if browser_instance:
            await browser_instance.close()

if __name__ == "__main__":
    # هنا هينادي عليها بـ None تلقائياً فيسحب كل حاجة
    asyncio.run(scrape_egibest())