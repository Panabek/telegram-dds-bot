import os
import requests
from fastapi import FastAPI, Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()
temp_storage = {}

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

def get_reference(sheet_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A:A"
    ).execute()

    values = result.get("values", [])
    return [row[0] for row in values if row]

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
            accounts = get_reference("Справочник_Счета")

            keyboard = []
            for acc in accounts:
                keyboard.append([{
                    "text": acc,
                    "callback_data": f"schet|{acc}"
                }])

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "Выберите счёт:",
                    "reply_markup": {
                        "inline_keyboard": keyboard
                    },
                },
            )

        # ✅ Выбор счёта
        elif action.startswith("schet|"):
            schet_value = action.replace("schet|", "")

            operations = get_reference("Справочник_Операции")

            keyboard = []
            for op in operations:
                keyboard.append([{
                    "text": op,
                    "callback_data": f"operacia|{op}|{schet_value}"
                }])

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт {schet_value} выбран.\nТеперь выберите операцию:",
                    "reply_markup": {
                        "inline_keyboard": keyboard
                    },
                },
            )
        
        # ✅ Выбор операции
        elif action.startswith("operacia|"):
            parts = action.split("|")
            operacia_text = parts[1]
            schet_value = parts[2]

            departments = get_reference("Справочник_Отделы")

            keyboard = []
            for dept in departments:
                keyboard.append([{
                    "text": dept,
                    "callback_data": f"otdel|{dept}|{schet_value}|{operacia_text}"
                }])

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт: {schet_value}\n"
                            f"Операция: {operacia_text}\n\n"
                            f"Выберите отдел/проект:",
                    "reply_markup": {
                        "inline_keyboard": keyboard
                    },
                },
            )
        
        # ✅ Выбор отдела
        elif action.startswith("otdel|"):
            parts = action.split("|")
            otdel_value = parts[1]
            schet_value = parts[2]
            operacia_text = parts[3]

            articles = get_reference("Справочник_Статьи")

            keyboard = []
            for art in articles:
                keyboard.append([{
                    "text": art,
                    "callback_data": f"state|{art}|{schet_value}|{operacia_text}|{otdel_value}"
                }])

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт: {schet_value}\n"
                            f"Операция: {operacia_text}\n"
                            f"Отдел: {otdel_value}\n\n"
                            f"Выберите статью:",
                    "reply_markup": {
                        "inline_keyboard": keyboard
                    },
                },
            )
            
        # ✅ Выбор статьи
        elif action.startswith("state|"):
            parts = action.split("|")
            state_value = parts[1]
            schet_value = parts[2]
            otdel_value = parts[4]
            operacia_text = parts[3]
            
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

        # Если пользователь вводит сумму
        if chat_id in temp_storage and "summa" not in temp_storage[chat_id]:
            try:
                amount = float(text.replace(",", "."))
            except:
                requests.post(
                    f"{TELEGRAM_API}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": "Введите корректную сумму числом:",
                    },
                )
                return {"ok": True}

            temp_storage[chat_id]["summa"] = amount

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "Введите комментарий:",
                },
            )

            return {"ok": True}

        # Если пользователь вводит комментарий
        if chat_id in temp_storage and "summa" in temp_storage[chat_id]:
            comment = text

            data_row = temp_storage[chat_id]

            values = [[
                data_row["schet"],
                data_row["operacia"],
                data_row["otdel"],
                data_row["state"],
                data_row["summa"],
                comment
            ]]

            service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=SHEET_NAME,
                valueInputOption="RAW",
                body={"values": values},
            ).execute()

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "✅ Операция успешно сохранена.",
                },
            )

            del temp_storage[chat_id]

            return {"ok": True}

        # Команда старт
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