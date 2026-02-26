import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def scrape_laroza_series(max_pages=None):
    all_series = [] 
    browser_instance = None
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]
    
    try:
        async with async_playwright() as p:
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                viewport={'width': 1280, 'height': 1000},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # ملاحظة: تركنا الصور مفعلة جزئياً (برمجياً) لكننا نمنع تحميل الملفات لتوفير البيانات
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())

            current_page = 1
            while True:
                # التحقق من سقف الصفحات لتجنب خطأ NoneType
                if max_pages is not None and current_page > max_pages:
                    break
                    
                url = f"https://laroza.makeup/moslslat4.php?page={current_page}"
                print(f"📡 جاري سحب مسلسلات لاروزا (صفحة {current_page})...")
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    if response and response.status == 404:
                        print(f"🛑 وصلنا لآخر صفحة عند {current_page-1}")
                        break

                    # --- تمرير تدريجي لتفعيل الـ Lazy Load الخاص بالصور في لاروزا ---
                    await page.evaluate("window.scrollBy(0, 1000)")
                    await asyncio.sleep(0.5)
                    await page.evaluate("window.scrollBy(0, 1000)")
                    
                    await page.wait_for_selector('li.col-xs-6', timeout=15000)
                    items = await page.query_selector_all('li.col-xs-6')
                    
                    if not items: break

                    for item in items:
                        try:
                            link_tag = await item.query_selector('h3 a')
                            if not link_tag: continue
                            
                            full_title = await link_tag.get_attribute('title') or await link_tag.inner_text()
                            
                            # فلتر الأمان
                            if any(word in full_title.lower() for word in blacklist):
                                continue

                            href = await link_tag.get_attribute('href')
                            
                            # جلب الصورة مع فحص جميع احتمالات الـ Lazy Loading
                            img_tag = await item.query_selector('img')
                            image_url = ""
                            if img_tag:
                                image_url = await img_tag.get_attribute('data-src') or \
                                            await img_tag.get_attribute('data-lazy-src') or \
                                            await img_tag.get_attribute('data-original') or \
                                            await img_tag.get_attribute('src')

                            # تنظيف الاسم واستخراج السنة
                            clean_name = full_title.replace("مشاهدة", "").replace("لاروزا", "").replace("مسلسل", "").strip()
                            year_match = re.search(r'(\d{4})', clean_name)
                            year = int(year_match.group(1)) if year_match else 2026
                            
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
                    print(f"⚠️ توقف السحب أو حدث خطأ في الصفحة {current_page}: {str(e)[:50]}")
                    break

    except asyncio.CancelledError:
        print("\n⚠️ تم قطع السحب يدوياً (Ctrl+C).. جاري حفظ البيانات المجمعة...")
    except Exception as e:
        print(f"\n❌ حدث خطأ غير متوقع: {e}")
    
    finally:
        # الحفظ النهائي المضمون
        if all_series:
            with open('laroza_series.json', 'w', encoding='utf-8') as f:
                json.dump(all_series, f, ensure_ascii=False, indent=4)
            print(f"✅ تم حفظ {len(all_series)} مسلسل من لاروزا بنجاح.")
        else:
            print("ℹ️ لم يتم جمع أي بيانات لحفظها.")
            
        if browser_instance:
            await browser_instance.close()

    return all_series

if __name__ == "__main__":
    try:
        # اتركها فارغة لسحب كل الصفحات، أو حدد رقماً (مثلاً max_pages=10)
        asyncio.run(scrape_laroza_series())
    except KeyboardInterrupt:
        pass