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

        # Убираем "часики"
        requests.post(
            f"{TELEGRAM_API}/answerCallbackQuery",
            json={"callback_query_id": callback_id},
        )

        # ➕ Добавить операцию
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

        # ✅ Выбор счёта
        elif action.startswith("schet_"):
            schet_value = action.replace("schet_", "")

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт {schet_value} выбран.\nТеперь выберите операцию:",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "Доход", "callback_data": f"operacia_income_{schet_value}"}],
                            [{"text": "Расход", "callback_data": f"operacia_expense_{schet_value}"}],
                        ]
                    },
                },
            )
        
        # ✅ Выбор операции
        elif action.startswith("operacia_"):
            parts = action.split("_")
            operacia_type = parts[1]      # income / expense
            schet_value = parts[2]

            operacia_text = "Доход" if operacia_type == "income" else "Расход"

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт: {schet_value}\nОперация: {operacia_text}\n\nВыберите отдел/проект:",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "Проект А", "callback_data": f"otdel_A_{schet_value}_{operacia_type}"}],
                            [{"text": "Проект B", "callback_data": f"otdel_B_{schet_value}_{operacia_type}"}],
                        ]
                    },
                },
            )
        
        # ✅ Выбор отдела
        elif action.startswith("otdel_"):
            parts = action.split("_")
            otdel_value = parts[1]
            schet_value = parts[2]
            operacia_type = parts[3]

            operacia_text = "Доход" if operacia_type == "income" else "Расход"

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт: {schet_value}\n"
                            f"Операция: {operacia_text}\n"
                            f"Отдел: {otdel_value}\n\n"
                            f"Выберите статью:",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "ГСМ", "callback_data": f"state_GSM_{schet_value}_{operacia_type}_{otdel_value}"}],
                            [{"text": "ЗП", "callback_data": f"state_ZP_{schet_value}_{operacia_type}_{otdel_value}"}],
                        ]
                    },
                },
            )
            
        # ✅ Выбор статьи
        elif action.startswith("state_"):
            parts = action.split("_")
            state_value = parts[1]
            schet_value = parts[2]
            operacia_type = parts[3]
            otdel_value = parts[4]

            operacia_text = "Доход" if operacia_type == "income" else "Расход"

            # Сохраняем данные временно в памяти
            global temp_storage
            try:
                temp_storage
            except:
                temp_storage = {}

            temp_storage[chat_id] = {
                "schet": schet_value,
                "operacia": operacia_text,
                "otdel": otdel_value,
                "state": state_value
            }

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт: {schet_value}\n"
                            f"Операция: {operacia_text}\n"
                            f"Отдел: {otdel_value}\n"
                            f"Статья: {state_value}\n\n"
                            f"Введите сумму:",
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