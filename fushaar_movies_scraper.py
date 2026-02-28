import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import os


async def scrape_fushaar(max_pages=None):
    all_media = []
    browser_instance = None  # لضمان إغلاق المتصفح لاحقاً وتنظيف الذاكرة
    blacklist = ["+18", "للكبار فقط", "جنس", "sex", "adult", "18+"]

    try:
        async with async_playwright() as p:
            # 1. تشغيل المتصفح مع إعدادات الأداء العالي
            browser_instance = await p.chromium.launch(headless=True)
            context = await browser_instance.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # 2. منع تحميل الصور لتسريع السحب بنسبة 300% (تحسين أداء)
            await page.route(
                "**/*.{png,jpg,jpeg,webp,gif}", lambda route: route.abort()
            )

            current_page = 1
            while max_pages is None or current_page <= max_pages:
                url = f"https://fushaar.forum/topvideos.php?&page={current_page}"
                print(f"📡 جاري سحب موقع فشار (صفحة {current_page})...")

                try:
                    response = await page.goto(
                        url, wait_until="domcontentloaded", timeout=90000
                    )
                    if response and response.status == 404:
                        print(f"🏁 تم الوصول لنهاية الصفحات عند {current_page - 1}")
                        break

                    await asyncio.sleep(2)  # انتظار بسيط لاستقرار الـ DOM

                    items = await page.query_selector_all("li.col-xs-6")
                    if not items:
                        print(f"🛑 لا توجد عناصر في صفحة {current_page}")
                        break

                    for item in items:
                        try:
                            title_tag = await item.query_selector("h3 a")
                            full_title = await title_tag.get_attribute("title")

                            # تصفية المحتوى
                            if not full_title or any(
                                word in full_title.lower() for word in blacklist
                            ):
                                continue

                            href = await title_tag.get_attribute("href")
                            img_tag = await item.query_selector("img")
                            image_url = (
                                await img_tag.get_attribute("src") if img_tag else ""
                            )

                            # استخراج السنة من العنوان
                            year_match = re.search(r"(\d{4})", full_title)
                            year = int(year_match.group(1)) if year_match else 2026

                            all_media.append(
                                {
                                    "name": f"[فشار] {full_title.strip()}",
                                    "url": href,
                                    "image_url": image_url,
                                    "year": year,
                                    "genre": "أفلام",
                                    "rating": 0.0,
                                    "createdAt": datetime.now().strftime(
                                        "%Y-%m-%dT%H:%M:%S"
                                    ),
                                }
                            )
                        except:
                            continue

                    print(f"✅ صفحة {current_page}: تم جمع {len(items)} فيلم.")
                    current_page += 1
                except Exception as e:
                    print(f"⚠️ خطأ في صفحة {current_page}: {e}")
                    break

    except Exception as e:
        print(f"❌ خطأ غير متوقع في المحرك الأساسي: {e}")

    finally:
        # --- التحسين رقم 2: قتل العمليات المعلقة (تنظيف الذاكرة) ---
        if browser_instance:
            await browser_instance.close()
            print("🔒 تم إغلاق المتصفح بنجاح وتطهير العمليات المعلقة.")

        # --- التحسين رقم 1: الحفظ بنظام الـ Chunks لضمان القبول على GitHub ---
        if all_media:
            # إزالة التكرار بناءً على الرابط
            unique_media = list({m["url"]: m for m in all_media}.values())
            total_count = len(unique_media)
            chunk_size = 10000

            print(f"📦 إجمالي الأفلام: {total_count}. جاري الحفظ والتقسيم...")

            for i in range(0, total_count, chunk_size):
                chunk = unique_media[i : i + chunk_size]
                part_num = (i // chunk_size) + 1
                filename = f"fushaar_movies_part{part_num}.json"

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=4)
                print(f"💾 تم حفظ الجزء {part_num} في: {filename}")
        else:
            print("ℹ️ لم يتم العثور على بيانات.")


if __name__ == "__main__":
    asyncio.run(scrape_fushaar())
