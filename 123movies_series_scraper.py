import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import os


async def scrape_123movies_series(max_pages=None):
    all_series = []
    browser_instance = None  # لضمان إغلاق المتصفح لاحقاً
    base_url = "https://ww8.123moviesfree.net/tv-series/"

    try:
        async with async_playwright() as p:
            # 1. تشغيل المتصفح مع معالجة الأداء
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # 2. منع تحميل الصور لتسريع العملية وتقليل استهلاك الرام
            await page.route(
                "**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort()
            )

            current_page = 1
            while True:
                if max_pages is not None and current_page > max_pages:
                    break

                url = f"{base_url}?page={current_page}"
                print(f"📡 سحب مسلسلات صفحة {current_page} من المصدر المباشر...")

                try:
                    response = await page.goto(
                        url, wait_until="domcontentloaded", timeout=90000
                    )
                    if response.status == 404:
                        print(f"🏁 وصلنا لنهاية الصفحات المتاحة عند {current_page - 1}")
                        break

                    await asyncio.sleep(2)  # انتظار بسيط لضمان استقرار العناصر

                    items = await page.query_selector_all("div.col")
                    if not items:
                        break

                    for item in items:
                        try:
                            # استخراج العنوان
                            title_tag = await item.query_selector("h2.card-title")
                            if not title_tag:
                                continue
                            title = await title_tag.inner_text()

                            # استخراج الرابط
                            link_tag = await item.query_selector("a.poster")
                            href = await link_tag.get_attribute("href")

                            # استخراج الصورة (data-src)
                            img_tag = await item.query_selector("img")
                            image_url = ""
                            if img_tag:
                                image_url = await img_tag.get_attribute(
                                    "data-src"
                                ) or await img_tag.get_attribute("src")

                            # استخراج السنة
                            year_match = re.search(r"(\d{4})", title)
                            year = int(year_match.group(1)) if year_match else 2026

                            all_series.append(
                                {
                                    "name": f"[123Movies] {title.strip()}",
                                    "url": (
                                        href
                                        if href.startswith("http")
                                        else f"https://ww8.123moviesfree.net{href}"
                                    ),
                                    "image_url": image_url,
                                    "year": year,
                                    "genre": "TV Series",
                                    "rating": 0.0,
                                    "createdAt": datetime.now().strftime(
                                        "%Y-%m-%dT%H:%M:%S"
                                    ),
                                }
                            )
                        except:
                            continue

                    print(f"✅ تم جمع {len(items)} مسلسل من صفحة {current_page}")
                    current_page += 1

                except Exception as e:
                    print(f"⚠️ خطأ في صفحة {current_page}: {e}")
                    break

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع في المحرك الأساسي: {e}")

    finally:
        # --- التحسين رقم 2: قتل العمليات المعلقة (تنظيف الذاكرة) ---
        if browser_instance:
            await browser_instance.close()
            print("🔒 تم إغلاق المتصفح بنجاح وتطهير العمليات المعلقة.")

        # --- حفظ البيانات بنظام التقسيم (Chunks) ---
        if all_series:
            # حذف أي تكرار ناتج عن تحديثات الموقع أثناء السحب
            unique_series = list({s["url"]: s for s in all_series}.values())
            total_count = len(unique_series)
            chunk_size = 10000

            print(f"📦 إجمالي المسلسلات: {total_count}. جاري الحفظ والتقسيم...")

            for i in range(0, total_count, chunk_size):
                chunk = unique_series[i : i + chunk_size]
                part_num = (i // chunk_size) + 1
                filename = f"123movies_series_part{part_num}.json"

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=4)
                print(f"💾 تم حفظ الجزء {part_num} في: {filename}")
        else:
            print("ℹ️ لم يتم العثور على أي مسلسلات.")


if __name__ == "__main__":
    asyncio.run(scrape_123movies_series())
