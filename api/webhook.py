import sys
import os

# bot_core.py loyiha ildizida joylashgan, uni topa olishi uchun yo'l qo'shamiz
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, Response
import bot_core

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
@app.route("/api/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return "Bot ishlayapti (webhook rejimida) ✅"

    try:
        update_json = request.get_json(force=True, silent=True)
        if update_json:
            bot_core.process_update(update_json)
    except Exception as e:
        # Xatoni log qilamiz, lekin Telegram'ga baribir 200 qaytaramiz —
        # aks holda Telegram qayta-qayta urinib, muammoni kuchaytiradi
        bot_core.logger.error(f"Webhook xatosi: {e}")

    return Response("OK", status=200)


# Vercel Python runtime Flask ilovasini avtomatik aniqlaydi ("app" o'zgaruvchisi)
