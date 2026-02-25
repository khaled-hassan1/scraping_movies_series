import asyncio
from playwright.async_api import async_playwright
import json

async def scrape_laroza():
    async with async_playwright() as p:
        # تشغيل المتصفح (headless=True للسرعة، أو False لو عايز تراقبه)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        url = "https://laroza.hair/home.24"
        print(f"🚀 جاري الدخول إلى لاروزا: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except:
            print("⚠️ الموقع استغرق وقت طويل، سأحاول البدء بالجمع...")

        movies_data = []
        titles_seen = set()

        # التمرير لجلب أكبر كمية من المحتوى
        print("⏬ جاري التمرير العميق لجلب المحتوى...")
        for i in range(20):  # زود الرقم ده لـ 100 لو عايز تجيب "كله" فعلياً
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(1.5)
            
            if i % 5 == 0:
                print(f"🔄 جاري المعالجة في التمريرة رقم {i}...")

        # استخراج الكروت (في لاروزا الكروت غالباً تكون داخل div بكلاس يحتوي على item أو video-box)
        # بناءً على بنية الموقع، سنبحث عن الروابط التي تحتوي على بوستر الفيلم
        cards = await page.query_selector_all('.Video-Content, .BoxItem, a:has(img)')

        print(f"🔎 تم العثور على {len(cards)} عنصر محتمل. جاري استخراج البيانات...")

        for card in cards:
            try:
                # جلب الرابط
                href = await card.get_attribute('href')
                if not href:
                    link_tag = await card.query_selector('a')
                    href = await link_tag.get_attribute('href') if link_tag else None
                
                # جلب الصورة والعنوان
                img_tag = await card.query_selector('img')
                if img_tag and href:
                    title = await img_tag.get_attribute('alt') or await img_tag.get_attribute('title')
                    img_url = await img_tag.get_attribute('src') or await img_tag.get_attribute('data-src')

                    if title and title not in titles_seen:
                        # تنظيف العناوين من كلمات مثل "مشاهدة" أو "تحميل" ليكون التطبيق احترافي
                        clean_title = title.replace("مشاهدة", "").replace("تحميل", "").replace("فيلم", "").strip()
                        
                        movies_data.append({
                            "title": clean_title,
                            "image": img_url if img_url.startswith('http') else f"https:{img_url}",
                            "url": href if href.startswith('http') else f"https://laroza.hair{href}"
                        })
                        titles_seen.add(title)
            except:
                continue

        # حفظ البيانات
        with open('laroza_content.json', 'w', encoding='utf-8') as f:
            json.dump(movies_data, f, ensure_ascii=False, indent=4)

        print(f"✅ اكتملت المهمة! تم جمع {len(movies_data)} عنوان من لاروزا.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_laroza())
