import os
import re
import json
import logging
from datetime import datetime, timedelta

import telebot
from telebot import types
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("modbot")

# ============================================================
#  SOZLAMALAR
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    try:
        BOT_TOKEN = input("8898545279:AAGmNE5gxjyNte-GtQ1zJYRYZhaBAQ_f7Cg").strip()
    except EOFError:
        BOT_TOKEN = ""

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi! Uni Vercel/lokal .env da yoki terminalda kiriting.")

WARN_LIMIT = int(os.environ.get("WARN_LIMIT", 3))
MUTE_MINUTES = int(os.environ.get("MUTE_MINUTES", 30))

# Upstash Redis (bepul) - saqlash uchun. Berilmasa, lokal fayl bilan ishlaydi
# (faqat lokal test uchun, Vercel'da fayl saqlanmaydi!).
UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)

# ============================================================
#  TA'QIQLANGAN SO'ZLAR / RUXSAT ETILGAN DOMENLAR
# ============================================================
BAD_WORDS = {
    "so'z1", "so'z2",
    # bu yerga o'zingizga kerakli haqoratli so'zlarni qo'shing (kichik harflarda)
}

ALLOWED_DOMAINS = {
    "t.me", "telegram.me", "telegram.org",
    "youtube.com", "youtu.be",
}

URL_REGEX = re.compile(
    r"(https?://[^\s]+)|(www\.[^\s]+)|"
    r"([a-zA-Z0-9-]+\.(?:uz|com|net|org|ru|io|me|xyz|top|click|info|biz)(?:/[^\s]*)?)",
    re.IGNORECASE,
)

# ============================================================
#  SAQLASH QATLAMI (Upstash Redis REST API yoki lokal fayl)
# ============================================================
LOCAL_FILE = "warnings.json"


def _local_load():
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _local_save(data):
    try:
        with open(LOCAL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Lokal faylga yozib bo'lmadi: {e}")


def _key(chat_id, user_id):
    return f"warn:{chat_id}:{user_id}"


def get_warning_count(chat_id, user_id):
    key = _key(chat_id, user_id)
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            r = requests.get(
                f"{UPSTASH_URL}/get/{key}",
                headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                timeout=5,
            )
            result = r.json().get("result")
            return int(result) if result else 0
        except Exception as e:
            logger.warning(f"Upstash get xato: {e}")
            return 0
    else:
        data = _local_load()
        return data.get(key, 0)


def increment_warning(chat_id, user_id):
    key = _key(chat_id, user_id)
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            r = requests.post(
                f"{UPSTASH_URL}/incr/{key}",
                headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                timeout=5,
            )
            return int(r.json().get("result", 0))
        except Exception as e:
            logger.warning(f"Upstash incr xato: {e}")
            return 0
    else:
        data = _local_load()
        data[key] = data.get(key, 0) + 1
        _local_save(data)
        return data[key]


def reset_warning(chat_id, user_id):
    key = _key(chat_id, user_id)
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            requests.post(
                f"{UPSTASH_URL}/set/{key}/0",
                headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                timeout=5,
            )
        except Exception as e:
            logger.warning(f"Upstash reset xato: {e}")
    else:
        data = _local_load()
        data[key] = 0
        _local_save(data)


# ============================================================
#  YORDAMCHI FUNKSIYALAR
# ============================================================
def contains_bad_word(text: str) -> bool:
    if not text:
        return False
    text_low = text.lower()
    words = re.findall(r"[a-zA-Zʼ'а-яА-ЯёЁ0-9]+", text_low)
    return any(w in BAD_WORDS for w in words)


def contains_bad_link(text: str) -> bool:
    if not text:
        return False
    for m in URL_REGEX.finditer(text):
        url = m.group(0)
        domain = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
        domain = domain.split("/")[0].lower().replace("www.", "")
        allowed = any(domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS)
        if not allowed:
            return True
    return False


def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


def mute_user(chat_id, user_id, minutes=MUTE_MINUTES):
    until = datetime.now() + timedelta(minutes=minutes)
    permissions = types.ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False,
    )
    bot.restrict_chat_member(chat_id, user_id, permissions=permissions, until_date=until)


# ============================================================
#  HANDLERLAR
# ============================================================
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    bot.reply_to(
        message,
        "Salom! Men guruh moderatori botiman.\n\n"
        "✅ Haqoratli so'z yoki notanish link bo'lgan xabarlarni o'chiraman.\n"
        f"✅ {WARN_LIMIT} marta ogohlantirishdan so'ng foydalanuvchi "
        f"{MUTE_MINUTES} daqiqaga mute qilinadi.\n\n"
        "Meni guruhga ADMIN qilib qo'shing va quyidagi huquqlarni bering:\n"
        "• Xabarlarni o'chirish (Delete messages)\n"
        "• A'zolarni cheklash (Ban/restrict users)",
    )


@bot.message_handler(func=lambda m: m.chat.type in ("group", "supergroup"), content_types=["text"])
def moderate(message):
    user = message.from_user
    chat_id = message.chat.id

    if is_admin(chat_id, user.id):
        return

    text = message.text or ""
    bad_word = contains_bad_word(text)
    bad_link = contains_bad_link(text)

    if not (bad_word or bad_link):
        return

    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception as e:
        logger.warning(f"Xabarni o'chirib bo'lmadi: {e}")

    count = increment_warning(chat_id, user.id)
    sabab = "haqoratli so'z" if bad_word else "notanish link"
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    if count < WARN_LIMIT:
        bot.send_message(
            chat_id,
            f"⚠️ {mention}, xabaringiz <b>{sabab}</b> tufayli o'chirildi.\n"
            f"Ogohlantirish: {count}/{WARN_LIMIT}",
        )
    else:
        try:
            mute_user(chat_id, user.id, MUTE_MINUTES)
            bot.send_message(
                chat_id,
                f"🔇 {mention} {MUTE_MINUTES} daqiqaga jim qilindi "
                f"({WARN_LIMIT} marta qoidabuzarlik).",
            )
            reset_warning(chat_id, user.id)
        except Exception as e:
            logger.error(f"Mute qilib bo'lmadi: {e}")
            bot.send_message(
                chat_id,
                f"{mention}, sizni cheklashga ruxsatim yo'q. Menga admin huquqini bering.",
            )


# ============================================================
#  Webhook orqali kelgan update'ni qayta ishlash
#  (bu funksiyani api/webhook.py chaqiradi)
# ============================================================
def process_update(update_json: dict):
    update = telebot.types.Update.de_json(update_json)
    bot.process_new_updates([update])


if __name__ == "__main__":
    print("Bot ishga tushmoqda...")
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")
