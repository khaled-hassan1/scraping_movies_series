import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def scrape_akoam(max_pages=None):
    all_movies = [] 
    browser_instance = None # تغيير الاسم لتجنب التضارب
    
    try:
        async with async_playwright() as p:
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
                    
                url = f"https://ak.sv/movies?page={current_page}"
                print(f"📡 جاري سحب الصفحة {current_page} من أكوام...")
                
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                    
                    if response.status == 404:
                        print(f"🛑 وصلنا لنهاية الصفحات عند الصفحة {current_page-1}")
                        break

                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
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
                            
                            created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                            all_movies.append({
                                "name": name.strip(),
                                "url": href if href.startswith('http') else f"https://ak.sv{href}",
                                "image_url": image_url,
                                "year": int(year_text.strip()) if year_text.strip().isdigit() else 2024,
                                "genre": ", ".join(genres) if genres else "عام",
                                "rating": float(rating_text.strip()) if rating_text else 0.0,
                                "createdAt": created_at
                            })
                        except Exception:
                            continue
                    
                    current_page += 1
                    
                except Exception as e:
                    print(f"⚠️ خطأ أثناء تحميل الصفحة {current_page}: {e}")
                    break

    except asyncio.CancelledError:
        print("\n⚠️ تم استلام إشارة إيقاف (CancelledError).")
    except Exception as e:
        print(f"\n❌ حدث خطأ غير متوقع: {e}")
    
    finally:
        # نقوم بالحفظ داخل الـ finally لضمان الحماية، لكن بدون return
        if all_movies:
            with open('akoam_movies.json', 'w', encoding='utf-8') as f:
                json.dump(all_movies, f, ensure_ascii=False, indent=4)
            print(f"\n✅ تم حفظ {len(all_movies)} فيلم في ملف akoam_movies.json")
        else:
            print("\nℹ️ لم يتم جمع أي بيانات لحفظها.")

    # الـ return الآن خارج بلوك الـ finally تماماً
    return all_movies

if __name__ == "__main__":
    try:
        asyncio.run(scrape_akoam())
    except KeyboardInterrupt:
        pass