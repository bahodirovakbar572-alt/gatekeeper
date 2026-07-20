"""
Bu skript Vercel'ga deploy qilingandan KEYIN, LOKAL kompyuteringizda
bir marta ishga tushiriladi. U Telegram'ga "mening bot yangilanishlarni
shu URL'ga yubor" deb aytadi.

Ishlatish:
    python set_webhook.py https://sizning-loyihangiz.vercel.app

BOT_TOKEN muhit o'zgaruvchisi (yoki .env fayl) orqali o'qiladi.
"""
import os
import sys
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("XATO: BOT_TOKEN topilmadi. Uni environment variable yoki .env faylga qo'ying.")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Foydalanish: python set_webhook.py https://sizning-loyihangiz.vercel.app")
    sys.exit(1)

base_url = sys.argv[1].rstrip("/")
webhook_url = f"{base_url}/api/webhook"

resp = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    data={"url": webhook_url},
    timeout=10,
)

print("Telegram javobi:", resp.json())

if resp.json().get("ok"):
    print(f"\n✅ Webhook muvaffaqiyatli o'rnatildi: {webhook_url}")
else:
    print("\n❌ Xatolik yuz berdi, javobni tekshiring.")
