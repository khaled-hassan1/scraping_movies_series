import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def scrape_akoam_series(max_pages=None):
    all_series = [] 
    browser_instance = None
    
    try:
        async with async_playwright() as p:
            # تشغيل المتصفح
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                viewport={'width': 1280, 'height': 1000},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            current_page = 1
            
            while True:
                if max_pages is not None and current_page > max_pages:
                    break
                    
                url = f"https://ak.sv/series?page={current_page}"
                print(f"📡 جاري سحب الصفحة {current_page} من مسلسلات أكوام...")
                
                try:
                    response = await page.goto(url, wait_until="networkidle", timeout=60000)
                    
                    if response.status == 404:
                        print(f"🛑 وصلنا لنهاية الصفحات عند الصفحة {current_page-1}")
                        break

                    # التمرير لأسفل لضمان تحميل الصور
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2) 

                    items = await page.query_selector_all('.entry-box')
                    
                    if not items:
                        break

                    for item in items:
                        try:
                            # 1. الاسم والرابط
                            title_tag = await item.query_selector('.entry-title a')
                            name = await title_tag.inner_text()
                            href = await title_tag.get_attribute('href')
                            
                            # 2. الصورة
                            img_tag = await item.query_selector('.entry-image img')
                            # نحاول جلب data-src أولاً للتعامل مع Lazy Loading
                            image_url = await img_tag.get_attribute('data-src') or await img_tag.get_attribute('src')
                            
                            # 3. التقييم
                            rating_tag = await item.query_selector('.label.rating')
                            rating_text = await rating_tag.inner_text() if rating_tag else "0.0"
                            
                            # 4. السنة (تأتي في الـ badge-secondary)
                            year_tag = await item.query_selector('.badge-secondary')
                            year_text = await year_tag.inner_text() if year_tag else str(datetime.now().year)
                            
                            # 5. التصنيفات
                            genre_tags = await item.query_selector_all('.badge-light')
                            genres = [await g.inner_text() for g in genre_tags]
                            
                            created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                            all_series.append({
                                "name": f"[مسلسل] {name.strip()}", # تمييزه كمسلسل
                                "url": href if href.startswith('http') else f"https://ak.sv{href}",
                                "image_url": image_url,
                                "year": int(year_text.strip()) if year_text.strip().isdigit() else 2024,
                                "genre": ", ".join(genres) if genres else "مسلسلات",
                                "rating": float(rating_text.strip()) if rating_text else 0.0,
                                "createdAt": created_at
                            })
                        except Exception:
                            continue
                    
                    current_page += 1
                    
                except Exception as e:
                    print(f"⚠️ خطأ في الصفحة {current_page}: {e}")
                    break

    except asyncio.CancelledError:
        print("\n⚠️ تم إيقاف سحب المسلسلات يدوياً.")
    except Exception as e:
        print(f"\n❌ حدث خطأ غير متوقع: {e}")
    
    finally:
        if browser_instance:
            await browser_instance.close()
            
        # حفظ ملف المسلسلات بشكل منفصل
        if all_series:
            with open('akoam_series.json', 'w', encoding='utf-8') as f:
                json.dump(all_series, f, ensure_ascii=False, indent=4)
            print(f"🏁 تم حفظ {len(all_series)} مسلسل في akoam_series.json")
            
    return all_series

if __name__ == "__main__":
    try:
        asyncio.run(scrape_akoam_series())
    except KeyboardInterrupt:
        pass