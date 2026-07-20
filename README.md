# Guruh moderatori bot (Telegram)

Bu bot guruhda:
- haqoratli so'z ishlatilgan xabarlarni,
- notanish (ruxsat etilmagan) link tashlangan xabarlarni

avtomatik o'chiradi, foydalanuvchini ogohlantiradi. 3 marta qoidabuzarlikdan
so'ng foydalanuvchi 30 daqiqaga **mute** qilinadi.

Bepul hostingda "uxlab qolmasligi" uchun bot o'zi ichida kichik web-server
(port ochadi) va har 5 daqiqada o'ziga so'rov yuboruvchi mexanizm bilan keladi.

---

## 1. Bot yaratish

1. Telegram'da **@BotFather** ga yozing.
2. `/newbot` buyrug'ini yuboring, nom va username bering.
3. Sizga beriladigan **TOKEN**ni saqlab qo'ying (masalan: `123456:ABC-DEF...`).

## 2. Botni guruhga qo'shish

1. Botni kerakli guruhga a'zo qiling.
2. Botni **admin** qiling va quyidagi huquqlarni yoqing:
   - Delete messages (xabarlarni o'chirish)
   - Ban/restrict users (a'zolarni cheklash / mute qilish)

## 3. Kodni sozlash

`bot.py` faylida:

- `BAD_WORDS` — ro'yxatga o'zingizga kerakli haqoratli so'zlarni qo'shing.
- `ALLOWED_DOMAINS` — link tashlashga ruxsat berilgan domenlar
  (masalan o'z kanalingiz, saytingiz).
- `WARN_LIMIT` va `MUTE_MINUTES` — environment variable orqali ham
  o'zgartirish mumkin (standart: 3 marta, 30 daqiqa).

## 4. Lokal ishga tushirish (sinov uchun)

```bash
pip install -r requirements.txt
export BOT_TOKEN="sizning_tokeningiz"
python bot.py
```

## 5. Bepul deploy — Render.com misolida

1. Loyihani GitHub repo'ga yuklang (`bot.py`, `requirements.txt`).
2. [render.com](https://render.com) da ro'yxatdan o'ting.
3. **New +** → **Web Service** → GitHub repo'ni tanlang.
4. Sozlamalar:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Instance Type**: Free
5. **Environment Variables** bo'limiga qo'shing:
   - `BOT_TOKEN` = sizning tokeningiz
   - `SELF_URL` = deploy tugagach beriladigan URL, masalan
     `https://mening-botim.onrender.com`
     (PORT o'zgaruvchisini Render avtomatik beradi, qo'lda kiritish shart emas)
6. Deploy tugagach, `SELF_URL` ni to'g'ri qiymat bilan yangilab, xizmatni
   qayta ishga tushiring (Manual Deploy → Redeploy).

> **Nega SELF_URL kerak?** Render kabi bepul tariflarda faollik bo'lmasa
> server "uxlab qoladi". Bot har 5 daqiqada shu URL'ga so'rov yuborib,
> serverni doim uyg'oq ushlab turadi.

## 6. Boshqa bepul platformalar

Xuddi shu kod quyidagilarda ham ishlaydi (PORT va BOT_TOKEN environment
variable sifatida beriladi):
- Railway.app
- Fly.io
- Replit (Always On funksiyasi bilan yoki self-ping bilan)

---

### Eslatma

- `BAD_WORDS` ro'yxati bo'sh namuna bilan kelgan — o'zingiz to'ldirishingiz kerak.
- Ogohlantirishlar `warnings.json` faylida saqlanadi. Bepul hostinglarning
  ko'pchiligida qayta deploy qilinganda fayl tizimi tozalanishi mumkin —
  agar doimiy saqlash kerak bo'lsa, keyinchalik SQLite yoki tashqi
  ma'lumotlar bazasiga (masalan, Supabase/PostgreSQL) o'tkazish tavsiya etiladi.
# gatekeeper
