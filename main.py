# import os
# import json
# import yt_dlp

# class YouTubeAudioScraper:
#     def __init__(self, channel_id):
#         # سنستخدم رابط الفيديوهات المباشر بدلاً من البلاي ليست لتجنب مشاكل الـ HLS
#         self.channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
#         self.download_path = 'youtube_audio_assets'
#         self.metadata_list = []
        
#         if not os.path.exists(self.download_path):
#             os.makedirs(self.download_path)

#     def start_scraping(self):
#         print(f"🚀 بدء السحب باستخدام وضع التوافق الأقصى...")

#         ydl_opts = {
#             'format': 'bestaudio/best',
#             'download_archive': 'downloaded_songs.txt', # يسجل الفيديوهات المحملة لعدم تكرارها
#             'outtmpl': f'{self.download_path}/%(id)s.%(ext)s',

#             'playlist_items': '1-2', # لتحميل أول مقطعين فقط للاختبار

#             # إعدادات تحويل الصوت لصيغتين
#             'postprocessors': [
#                 {
#                     'key': 'FFmpegExtractAudio',
#                     'preferredcodec': 'm4a',
#                     'preferredquality': '128',
#                 },
#                 # إذا كنت تريد النسختين معاً، ستحتاج لتشغيل المعالج مرتين أو استخدام سكريبت خارجي
#             ],
#         }

#         try:
#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 # استخراج البيانات
#                 result = ydl.extract_info(self.channel_url, download=True)
                
#                 # معالجة النتائج سواء كانت قناة أو قائمة
#                 if 'entries' in result:
#                     entries = result['entries']
#                 else:
#                     entries = [result]

#                 for entry in entries:
#                     if entry:
#                         data = {
#                             'id': entry.get('id'),
#                             'title': entry.get('title'),
#                             'duration': entry.get('duration'),
#                             'thumbnail': entry.get('thumbnail'),
#                             'audio_file': f"{entry.get('id')}.m4a",
#                             'original_url': f"https://www.youtube.com/watch?v={entry.get('id')}"
#                         }
#                         self.metadata_list.append(data)
#                         print(f"✅ تم تحميل وحفظ: {data['title']}")

#         except Exception as e:
#             print(f"❌ حدث خطأ غير متوقع: {e}")
        
#         self.save_metadata_to_json()

#     def save_metadata_to_json(self):
#         filename = 'final_metadata.json'
#         with open(filename, 'w', encoding='utf-8') as f:
#             json.dump(self.metadata_list, f, ensure_ascii=False, indent=4)
#         print(f"\n✨ العملية انتهت. الملفات في مجلد: {self.download_path}")

# if __name__ == "__main__":
#     CHANNEL_ID = "UCmMcOjsVehVlEOteyrhjI2Q"
#     scraper = YouTubeAudioScraper(CHANNEL_ID)
#     scraper.start_scraping()


import os
import json
import yt_dlp
from supabase import create_client # ستحتاج لتثبيتها pip install supabase

class YouTubeAudioScraper:
    def __init__(self, channel_id):
        self.channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        self.download_path = 'audio_assets'
        # بيانات السوبابيس (تحصل عليها من موقع Supabase مجاناً)
        self.url = "YOUR_SUPABASE_URL"
        self.key = "YOUR_SUPABASE_KEY"
        self.supabase = create_client(self.url, self.key)

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def start_scraping(self):
        ydl_opts = {
            'format': 'bestaudio/best',
            'download_archive': 'downloaded_archive.txt', # هام جداً لعدم تكرار التحميل
            'outtmpl': f'{self.download_path}/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '128',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # نسحب آخر 10 فيديوهات فقط كل أسبوع لتوفير الوقت والموارد
            result = ydl.extract_info(self.channel_url, download=True)
            entries = result.get('entries', [result])

            for entry in entries:
                if entry:
                    video_id = entry.get('id')
                    file_path = f"{self.download_path}/{video_id}.m4a"
                    
                    if os.path.exists(file_path):
                        # 1. ارفع الملف الصوتي لـ Supabase Storage
                        public_url = self.upload_to_storage(file_path, video_id)
                        
                        # 2. احفظ البيانات في Database
                        self.save_to_database(entry, public_url)
                        
                        # 3. احذف الملف من السيرفر (GitHub) لتوفير المساحة
                        os.remove(file_path)

    def upload_to_storage(self, file_path, video_id):
        with open(file_path, 'rb') as f:
            self.supabase.storage.from_('audios').upload(f"{video_id}.m4a", f)
        return self.supabase.storage.from_('audios').get_public_url(f"{video_id}.m4a")

    def save_to_database(self, entry, audio_url):
        data = {
            "video_id": entry['id'],
            "title": entry['title'],
            "duration": entry['duration'],
            "thumbnail": entry['thumbnail'],
            "audio_url": audio_url
        }
        self.supabase.table('quran_audios').upsert(data).execute()