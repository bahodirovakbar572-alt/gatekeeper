import os
import re
import json
import threading
import logging
from datetime import datetime, timedelta

import telebot
from telebot import types

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("modbot")

# ============================================================
#  SOZLAMALAR
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi! Uni sozlang.")

WARN_LIMIT = int(os.environ.get("WARN_LIMIT", 3))       # nechta ogohlantirishdan keyin mute
MUTE_MINUTES = int(os.environ.get("MUTE_MINUTES", 30))  # necha daqiqaga mute
WARNINGS_FILE = "warnings.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ============================================================
#  TA'QIQLANGAN SO'ZLAR
#  Bu yerga o'zingizga kerakli haqoratli so'zlarni qo'shing (kichik harflarda)
# ============================================================
BAD_WORDS = {
    "so'z1", "so'z2",
}

# Ruxsat etilgan domenlar — shu domenlarga link tashlash mumkin
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
#  OGOHLANTIRISHLARNI SAQLASH (oddiy JSON fayl)
# ============================================================
lock = threading.Lock()


def load_warnings():
    if os.path.exists(WARNINGS_FILE):
        try:
            with open(WARNINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_warnings(data):
    with open(WARNINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


warnings_data = load_warnings()


def get_key(chat_id, user_id):
    return f"{chat_id}_{user_id}"


def add_warning(chat_id, user_id):
    with lock:
        key = get_key(chat_id, user_id)
        warnings_data[key] = warnings_data.get(key, 0) + 1
        save_warnings(warnings_data)
        return warnings_data[key]


def reset_warning(chat_id, user_id):
    with lock:
        key = get_key(chat_id, user_id)
        warnings_data[key] = 0
        save_warnings(warnings_data)


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
        "• Xabarlarni o'chirish\n"
        "• A'zolarni cheklash",
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

    count = add_warning(chat_id, user.id)
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
#  ISHGA TUSHIRISH
# ============================================================
if __name__ == "__main__":
    logger.info("Bot ishga tushdi...")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
