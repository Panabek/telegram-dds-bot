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

    # Обработка обычного сообщения
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