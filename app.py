import os
import requests
from fastapi import FastAPI, Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()

# ====== НАСТРОЙКИ ======
SPREADSHEET_ID = "1FpFdW7vrl_RJjSTRJm5dSI5gBWzZD3SwhPAot428BOU"
SHEET_NAME = "Лист15"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

import json
import os

creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])

credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=SCOPES,
)

service = build("sheets", "v4", credentials=credentials)

BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


@app.post("/")
async def webhook(request: Request):
    data = await request.json()

    # 1️⃣ Обработка нажатия кнопки
    if "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        callback_id = callback["id"]
        action = callback["data"]

        # Убираем "часики" у кнопки
        requests.post(
            f"{TELEGRAM_API}/answerCallbackQuery",
            json={"callback_query_id": callback_id},
        )

        if action == "add_operation":
            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "Выберите счёт:",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "1010", "callback_data": "schet_1010"}],
                            [{"text": "1030", "callback_data": "schet_1030"}],
                        ]
                    },
                },
            )

        return {"ok": True}

    # 2️⃣ Обработка команды /start
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "➕ Добавить операцию", "callback_data": "add_operation"}]
                ]
            }

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "Выберите действие:",
                    "reply_markup": keyboard
                },
            )

        return {"ok": True}

    return {"ok": True}