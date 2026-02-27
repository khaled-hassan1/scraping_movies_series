import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import os

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
            
            # منع الصور لتسريع العملية
            await page.route("**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort())
            
            current_page = 1
            while True:
                if max_pages is not None and current_page > max_pages:
                    break
                    
                url = f"https://ak.sv/series?page={current_page}"
                print(f"📡 جاري سحب الصفحة {current_page} من مسلسلات أكوام...")
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                    
                    if response.status == 404:
                        print(f"🛑 وصلنا لنهاية الصفحات عند الصفحة {current_page-1}")
                        break

                    # انتظار بسيط للتأكد من وجود العناصر
                    await asyncio.sleep(2) 

                    items = await page.query_selector_all('.entry-box')
                    if not items:
                        break

                    for item in items:
                        try:
                            title_tag = await item.query_selector('.entry-title a')
                            name = await title_tag.inner_text()
                            href = await title_tag.get_attribute('href')
                            
                            img_tag = await item.query_selector('.entry-image img')
                            image_url = await img_tag.get_attribute('data-src') or await img_tag.get_attribute('src')
                            
                            rating_tag = await item.query_selector('.label.rating')
                            rating_text = await rating_tag.inner_text() if rating_tag else "0.0"
                            
                            year_tag = await item.query_selector('.badge-secondary')
                            year_text = await year_tag.inner_text() if year_tag else str(datetime.now().year)
                            
                            genre_tags = await item.query_selector_all('.badge-light')
                            genres = [await g.inner_text() for g in genre_tags]
                            
                            all_series.append({
                                "name": f"[أكوام] {name.strip()}",
                                "url": href if href.startswith('http') else f"https://ak.sv{href}",
                                "image_url": image_url,
                                "year": int(year_text.strip()) if year_text.strip().isdigit() else 2026,
                                "genre": ", ".join(genres) if genres else "مسلسلات",
                                "rating": float(rating_text.strip()) if rating_text else 0.0,
                                "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            })
                        except:
                            continue
                    
                    current_page += 1
                    
                except Exception as e:
                    print(f"⚠️ خطأ في الصفحة {current_page}: {e}")
                    break

    except Exception as e:
        print(f"\n❌ حدث خطأ غير متوقع: {e}")
    
    finally:
        # 1. إغلاق المتصفح فوراً (حل مشكلة العمليات المعلقة)
        if browser_instance:
            await browser_instance.close()
            print("🔒 تم إغلاق المتصفح وتطهير العمليات.")
            
        # 2. حفظ البيانات بنظام التقسيم (Chunks)
        if all_series:
            # حذف التكرار بناءً على الرابط
            unique_series = list({s['url']: s for s in all_series}.values())
            chunk_size = 10000
            
            for i in range(0, len(unique_series), chunk_size):
                chunk = unique_series[i : i + chunk_size]
                part = (i // chunk_size) + 1
                filename = f'akoam_series_part{part}.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=4)
                print(f"💾 تم حفظ {len(chunk)} مسلسل في {filename}")
        else:
            print("ℹ️ لم يتم العثور على أي مسلسلات.")
            
    return all_series

if __name__ == "__main__":
    asyncio.run(scrape_akoam_series())