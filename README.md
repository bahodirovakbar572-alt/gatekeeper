# Telegram moderator bot — Vercel'ga bepul deploy (webhook rejimi)

Bu versiya avvalgi (Render/polling) versiyadan farqli o'laroq **webhook**
orqali ishlaydi: bot doim "uyg'oq" turishi shart emas, Telegram xabar
yuborganda avtomatik ishga tushadi. Shu sababli self-ping yoki
instance-hours kabi muammolar umuman bo'lmaydi — Vercel'ning bepul
tarifi bunday yengil botlar uchun juda mos.

## Fayllar tuzilishi

```
modbot_webhook/
├── api/
│   └── webhook.py      ← Vercel serverless funksiyasi (kirish nuqtasi)
├── bot_core.py          ← Bot logikasi (moderatsiya, mute va h.k.)
├── set_webhook.py        ← Deploy'dan keyin bir marta ishga tushiriladi
├── requirements.txt
├── vercel.json
└── README.md (shu fayl)
```

---

## 1-qadam — Bot yaratish (agar hali yaratmagan bo'lsangiz)

1. Telegram'da **@BotFather** ga yozing → `/newbot` → nom bering.
2. Sizga beriladigan **TOKEN**ni saqlang.
3. ⚠️ Eski tokeningiz avval oshkor bo'lgan bo'lsa, albatta uni
   **revoke** qilib, yangisini oling (`/mybots` → botingiz → API Token →
   Revoke current token).

## 2-qadam — Upstash Redis (bepul) — ogohlantirishlarni saqlash uchun

Vercel'ning serverless funksiyalari hech qanday faylni saqlamaydi, shu
sababli ogohlantirishlar sonini tashqi joyda saqlash kerak.

1. [upstash.com](https://upstash.com) saytiga kiring, bepul ro'yxatdan o'ting.
2. **Create Database** → Redis → istalgan nom bering, region tanlang.
3. Baza sahifasida **REST API** bo'limidan quyidagi ikkita qiymatni oling:
   - `UPSTASH_REDIS_REST_URL`
   - `UPSTASH_REDIS_REST_TOKEN`

Bularsiz ham bot ishlaydi, lekin ogohlantirish hisobi doim 0'dan
boshlanaveradi (chunki hech narsa saqlanmaydi).

## 3-qadam — GitHub'ga yuklash

```bash
cd modbot_webhook
git init
git add .
git commit -m "Telegram moderator bot - webhook versiyasi"
```

GitHub'da yangi repo yarating va shu papkani unga push qiling.

## 4-qadam — Vercel'ga deploy qilish

1. [vercel.com](https://vercel.com) ga kiring, GitHub orqali ro'yxatdan o'ting.
2. **Add New** → **Project** → GitHub repo'ingizni tanlang → **Import**.
3. **Environment Variables** bo'limiga qo'shing:
   | Nomi | Qiymati |
   |---|---|
   | `BOT_TOKEN` | Sizning bot tokeningiz |
   | `UPSTASH_REDIS_REST_URL` | Upstash'dan olingan URL |
   | `UPSTASH_REDIS_REST_TOKEN` | Upstash'dan olingan token |
4. **Deploy** tugmasini bosing.
5. Deploy tugagach, Vercel sizga URL beradi, masalan:
   `https://mening-botim.vercel.app`

## 5-qadam — Webhookni ro'yxatdan o'tkazish

Lokal kompyuteringizda (`modbot_webhook` papkasida):

```bash
pip install -r requirements.txt
python set_webhook.py https://mening-botim.vercel.app
```

Muvaffaqiyatli bo'lsa, shunday xabar chiqadi:
```
✅ Webhook muvaffaqiyatli o'rnatildi: https://mening-botim.vercel.app/api/webhook
```

## 6-qadam — Botni sinash

1. Botni guruhga qo'shing va **admin** qiling:
   - Delete messages ✅
   - Ban/restrict users ✅
2. Guruhda `BAD_WORDS` ro'yxatidagi so'zni yozib ko'ring — xabar
   o'chishi va ogohlantirish kelishi kerak.

---

## Sozlash

`bot_core.py` faylida:
- `BAD_WORDS` — ta'qiqlangan so'zlar ro'yxatini to'ldiring.
- `ALLOWED_DOMAINS` — ruxsat etilgan domenlar.
- `WARN_LIMIT`, `MUTE_MINUTES` — Vercel Environment Variables orqali ham
  o'zgartirish mumkin (standart: 3 marta, 30 daqiqa).

O'zgartirish kiritgach, GitHub'ga push qilsangiz Vercel avtomatik qayta
deploy qiladi — qo'lda hech narsa qilish shart emas.

## Nega bu usul Render'dagidan yaxshiroq?

- ❌ Instance-hours tugash muammosi yo'q (bot doim ishlab turmaydi).
- ❌ Self-ping kerak emas (webhook — event asosida ishlaydi).
- ❌ "Suspended" bo'lish xavfi deyarli yo'q (Vercel'ning bepul tarifi
  bunday yengil trafik uchun juda katta zaxiraga ega).
- ✅ Ogohlantirishlar Upstash Redis'da doimiy saqlanadi (qayta deploy
  qilinsa ham yo'qolmaydi).

## Lokal test (ixtiyoriy)

Webhook'ni lokal test qilish qiyinroq (tashqi URL kerak bo'ladi,
masalan `ngrok` orqali). Oddiy funksional tekshiruv uchun avvalgi
polling versiyasidagi `bot.py`'dan foydalanishingiz mumkin — u ham
xuddi shu `BAD_WORDS`/`ALLOWED_DOMAINS` mantig'iga ega.
