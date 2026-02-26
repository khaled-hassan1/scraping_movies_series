import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_egibest(max_pages=None):
    all_movies = [] 
    browser = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            current_page = 1
            while True:
                # شرط التوقف لو حددنا max_pages
                if max_pages is not None and current_page > max_pages:
                    break
                    
                url = f"https://egibest.live/category/movies/page/{current_page}/"
                print(f"📡 جاري سحب إيجي بست (صفحة {current_page})...")
                
                try:
                    response = await page.goto(url, wait_until="commit", timeout=60000)
                    if response.status == 404: break

                    await page.wait_for_selector('a.postBlockCol', timeout=10000)
                    items = await page.query_selector_all('a.postBlockCol')
                    if not items: break

                    for item in items:
                        try:
                            title = await item.get_attribute('title') or await (await item.query_selector('h3.title')).inner_text()
                            if any(word in title.lower() for word in blacklist): continue

                            href = await item.get_attribute('href')
                            img_tag = await item.query_selector('img')
                            image_url = await img_tag.get_attribute('src') if img_tag else ""
                            
                            clean_name = title.replace("مشاهدة", "").replace("إيجي بست", "").replace("مترجم اونلاين", "").strip()
                            year_match = re.search(r'(\d{4})', clean_name)
                            
                            all_movies.append({
                                "name": f"[EgiBest] {clean_name}",
                                "url": href,
                                "image_url": image_url,
                                "year": int(year_match.group(1)) if year_match else 2025,
                                "genre": "أفلام",
                                "rating": 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except: continue
                    
                    current_page += 1
                    await asyncio.sleep(0.5) # سرعة معقولة

                except Exception as e:
                    print(f"⚠️ انتهت الصفحات أو حدث خطأ بسيط: {e}")
                    break

    except asyncio.CancelledError:
        print("\n⚠️ تم إيقاف السحب يدوياً (Ctrl+C). جاري حفظ ما تم جمعه...")
    except Exception as e:
        print(f"\n❌ حدث خطأ غير متوقع: {e}")
    
    finally:
        # السطر ده هيتنفذ في كل الحالات (لو قفلت البرنامج أو لو خلص)
        if all_movies:
            with open('egibest_movies.json', 'w', encoding='utf-8') as f:
                json.dump(all_movies, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(all_movies)} فيلم في egibest_movies.json")
        else:
            print("ℹ️ لم يتم جمع أي بيانات لحفظها.")
        
        if browser:
            await browser.close()

if __name__ == "__main__":
    try:
        # هنا تقدر تسيبه يسحب للأبد أو تحدد رقم
        asyncio.run(scrape_egibest(max_pages=None)) 
    except KeyboardInterrupt:
        # لمنع ظهور رسالة الخطأ الطويلة في التيرمينال عند القفل يدوياً
        pass