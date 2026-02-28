import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import os


async def scrape_egibest(max_pages=None):
    all_movies = []
    browser_instance = None  # لضمان إغلاق المتصفح لاحقاً
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]

    try:
        async with async_playwright() as p:
            # 1. تشغيل المتصفح مع إعدادات الأداء العالي
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # 2. منع تحميل الصور لتسريع السحب وتوفير الرام (تحسين أداء)
            await page.route(
                "**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort()
            )

            current_page = 1
            while True:
                if max_pages is not None and current_page > max_pages:
                    break

                url = f"https://egibest.live/movies/page/{current_page}/"
                print(f"📡 جاري سحب إيجي بست (صفحة {current_page})...")

                try:
                    response = await page.goto(
                        url, wait_until="domcontentloaded", timeout=90000
                    )

                    if response.status == 404:
                        print(f"🏁 وصلنا لنهاية الصفحات عند الصفحة {current_page}")
                        break

                    await asyncio.sleep(2)  # انتظار بسيط لاستقرار العناصر

                    # السيلكتور الجديد بناءً على ملف ع.txt
                    items = await page.query_selector_all("a.postBlockCol")

                    if not items:
                        print(f"🛑 لا يوجد المزيد من العناصر عند صفحة {current_page}")
                        break

                    for item in items:
                        try:
                            title_tag = await item.query_selector("h3.title")
                            title = await title_tag.inner_text() if title_tag else ""

                            if not title or any(
                                word in title.lower() for word in blacklist
                            ):
                                continue

                            href = await item.get_attribute("href")
                            img_tag = await item.query_selector("img")
                            image_url = (
                                await img_tag.get_attribute("src") if img_tag else ""
                            )

                            rating_tag = await item.query_selector("span.r i.rating i")
                            rating = (
                                await rating_tag.inner_text() if rating_tag else "0.0"
                            )

                            clean_name = (
                                title.replace("مشاهدة", "")
                                .replace("فيلم", "")
                                .replace("مترجم", "")
                                .strip()
                            )
                            year_match = re.search(r"(\d{4})", clean_name)
                            year = int(year_match.group(1)) if year_match else 2026

                            all_movies.append(
                                {
                                    "name": f"[EgiBest] {clean_name}",
                                    "url": href,
                                    "image_url": image_url,
                                    "year": year,
                                    "genre": "أفلام",
                                    "rating": float(rating) if rating else 0.0,
                                    "createdAt": datetime.now().strftime(
                                        "%Y-%m-%dT%H:%M:%S"
                                    ),
                                }
                            )
                        except:
                            continue

                    print(f"✅ تم سحب {len(items)} عنصر من صفحة {current_page}")
                    current_page += 1

                except Exception as e:
                    print(f"❌ خطأ في صفحة {current_page}: {e}")
                    break

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع في المحرك: {e}")

    finally:
        # --- التحسين رقم 2: قتل العمليات المعلقة (تنظيف الذاكرة) ---
        if browser_instance:
            await browser_instance.close()
            print("🔒 تم إغلاق المتصفح بنجاح وتنظيف العمليات اليتيمة.")

        # --- الحفظ بنظام الـ Chunks لضمان القبول على GitHub ---
        if all_movies:
            unique_movies = list({m["url"]: m for m in all_movies}.values())
            total_count = len(unique_movies)
            chunk_size = 10000

            print(f"📦 إجمالي الأفلام: {total_count}. جاري الحفظ والتقسيم...")

            for i in range(0, total_count, chunk_size):
                chunk = unique_movies[i : i + chunk_size]
                part_num = (i // chunk_size) + 1
                filename = f"egibest_movies_part{part_num}.json"

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=4)
                print(f"💾 تم حفظ الجزء {part_num} في: {filename}")
        else:
            print("ℹ️ لم يتم العثور على أي بيانات.")


if __name__ == "__main__":
    asyncio.run(scrape_egibest())
