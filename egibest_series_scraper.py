import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_egibest_series(max_pages=None):
    all_series = [] 
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                viewport={'width': 1280, 'height': 1000},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # حظر الصور لتسريع العملية
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            current_page = 1
            while True:
                # التحقق من الحد الأقصى للصفحات (إذا وُجد)
                if max_pages is not None and current_page > max_pages:
                    break
                    
                url = f"https://egibest.live/category/series/page/{current_page}/"
                print(f"📡 جاري سحب مسلسلات إيجي بست (صفحة {current_page})...")
                
                try:
                    response = await page.goto(url, wait_until="commit", timeout=60000)
                    
                    if response.status == 404:
                        print(f"🛑 وصلنا لآخر صفحة متاح عند {current_page-1}")
                        break

                    # انتظار تحميل العناصر
                    await page.wait_for_selector('a.postBlockCol', timeout=15000)
                    items = await page.query_selector_all('a.postBlockCol')
                    
                    if not items: break

                    for item in items:
                        try:
                            # جلب العنوان
                            title = await item.get_attribute('title')
                            if not title:
                                h3 = await item.query_selector('h3.title')
                                title = await h3.inner_text() if h3 else "بدون عنوان"
                            
                            if any(word in title.lower() for word in blacklist):
                                continue

                            href = await item.get_attribute('href')
                            img_tag = await item.query_selector('img')
                            image_url = await img_tag.get_attribute('src') if img_tag else ""
                            
                            # التقييم
                            rating_val = 0.0
                            rating_tag = await item.query_selector('i.rating i')
                            if rating_tag:
                                r_text = await rating_tag.inner_text()
                                rating_val = float(r_text.strip()) if r_text.strip() else 0.0

                            # تنظيف الاسم والسنة
                            clean_name = title.replace("مشاهدة", "").replace("إيجي بست", "").replace("مسلسل", "").strip()
                            year_match = re.search(r'(\d{4})', clean_name)
                            year = int(year_match.group(1)) if year_match else 2025
                            
                            all_series.append({
                                "name": f"[مسلسل] {clean_name}",
                                "url": href,
                                "image_url": image_url,
                                "year": year,
                                "genre": "مسلسلات",
                                "rating": rating_val,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except:
                            continue
                    
                    current_page += 1
                    await asyncio.sleep(0.5) # راحة بسيطة للموقع
                    
                except Exception as e:
                    print(f"⚠️ توقف عند الصفحة {current_page}")
                    break

    except asyncio.CancelledError:
        print("\n⚠️ تم قطع السحب يدوياً.. جاري حفظ البيانات المجمعة...")
    except Exception as e:
        print(f"\n❌ حدث خطأ غير متوقع: {e}")
    
    finally:
        # الحفظ النهائي في كل الحالات
        if all_series:
            with open('egibest_series.json', 'w', encoding='utf-8') as f:
                json.dump(all_series, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(all_series)} مسلسل من إيجي بست بنجاح.")
        else:
            print("ℹ️ لم يتم العثور على أي بيانات لحفظها.")
        
        if browser_instance:
            await browser_instance.close()

    return all_series

if __name__ == "__main__":
    try:
        # اتركها فارغة لسحب كل الصفحات، أو ضع رقماً مثل (max_pages=10)
        asyncio.run(scrape_egibest_series())
    except KeyboardInterrupt:
        pass