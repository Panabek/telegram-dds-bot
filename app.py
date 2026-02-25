import os
import requests
from datetime import datetime, timedelta
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

def get_reference(sheet_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A:A"
    ).execute()

    values = result.get("values", [])
    return [row[0] for row in values if row]

BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

temp_storage = {}

def build_keyboard(items, prefix):
    keyboard = []
    for i, item in enumerate(items):
        keyboard.append([{
            "text": item,
            "callback_data": f"{prefix}|{i}"
        }])
    return {"inline_keyboard": keyboard}


@app.post("/")
async def webhook(request: Request):
    data = await request.json()

    # ================= CALLBACK =================
    if "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        callback_id = callback["id"]
        action = callback["data"]

        requests.post(
            f"{TELEGRAM_API}/answerCallbackQuery",
            json={"callback_query_id": callback_id},
        )

        # ===== СТАРТ ДОБАВЛЕНИЯ =====
        if action == "add_operation":
            accounts = get_reference("Справочник_Счета")
            temp_storage[chat_id] = {"accounts": accounts}

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "Выберите счёт:",
                    "reply_markup": build_keyboard(accounts, "schet")
                },
            )

        # ===== СЧЁТ =====
        elif action.startswith("schet|"):
            index = int(action.split("|")[1])
            schet_value = temp_storage[chat_id]["accounts"][index]

            operations = get_reference("Справочник_Операции")

            temp_storage[chat_id].update({
                "schet": schet_value,
                "operations": operations
            })

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт: {schet_value}\nВыберите операцию:",
                    "reply_markup": build_keyboard(operations, "operacia")
                },
            )

        # ===== ОПЕРАЦИЯ =====
        elif action.startswith("operacia|"):
            index = int(action.split("|")[1])
            operacia_value = temp_storage[chat_id]["operations"][index]

            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            temp_storage[chat_id].update({
                "operacia": operacia_value,
                "today": today,
                "yesterday": yesterday
            })

            keyboard = {
                "inline_keyboard": [
                    [{"text": f"Сегодня ({today})", "callback_data": "date|today"}],
                    [{"text": f"Вчера ({yesterday})", "callback_data": "date|yesterday"}],
                    [{"text": "Ввести вручную", "callback_data": "date|manual"}],
                ]
            }

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт: {temp_storage[chat_id]['schet']}\n"
                            f"Операция: {operacia_value}\n\n"
                            f"Выберите дату:",
                    "reply_markup": keyboard
                },
            )

        # ===== ДАТА =====
        elif action.startswith("date|"):
            choice = action.split("|")[1]

            if choice == "today":
                selected_date = temp_storage[chat_id]["today"]
            elif choice == "yesterday":
                selected_date = temp_storage[chat_id]["yesterday"]
            else:
                temp_storage[chat_id]["awaiting_manual_date"] = True

                requests.post(
                    f"{TELEGRAM_API}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": "Введите дату в формате YYYY-MM-DD:",
                    },
                )
                return {"ok": True}

            temp_storage[chat_id]["date"] = selected_date

            departments = get_reference("Справочник_Отделы")
            temp_storage[chat_id]["departments"] = departments

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Дата: {selected_date}\n\nВыберите отдел:",
                    "reply_markup": build_keyboard(departments, "otdel")
                },
            )

        # ===== ОТДЕЛ =====
        elif action.startswith("otdel|"):
            index = int(action.split("|")[1])
            otdel_value = temp_storage[chat_id]["departments"][index]

            articles = get_reference("Справочник_Статьи")

            temp_storage[chat_id].update({
                "otdel": otdel_value,
                "articles": articles
            })

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт: {temp_storage[chat_id]['schet']}\n"
                            f"Операция: {temp_storage[chat_id]['operacia']}\n"
                            f"Дата: {temp_storage[chat_id]['date']}\n"
                            f"Отдел: {otdel_value}\n\n"
                            f"Выберите статью:",
                    "reply_markup": build_keyboard(articles, "state")
                },
            )

        # ===== СТАТЬЯ =====
        elif action.startswith("state|"):
            index = int(action.split("|")[1])
            state_value = temp_storage[chat_id]["articles"][index]

            temp_storage[chat_id]["state"] = state_value

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Счёт: {temp_storage[chat_id]['schet']}\n"
                            f"Операция: {temp_storage[chat_id]['operacia']}\n"
                            f"Дата: {temp_storage[chat_id]['date']}\n"
                            f"Отдел: {temp_storage[chat_id]['otdel']}\n"
                            f"Статья: {state_value}\n\n"
                            f"Введите сумму:",
                },
            )

        return {"ok": True}

    # ================= MESSAGE =================
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # ===== РУЧНАЯ ДАТА =====
        if chat_id in temp_storage and temp_storage[chat_id].get("awaiting_manual_date"):
            temp_storage[chat_id]["date"] = text
            temp_storage[chat_id]["awaiting_manual_date"] = False

            departments = get_reference("Справочник_Отделы")
            temp_storage[chat_id]["departments"] = departments

            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"Дата: {text}\n\nВыберите отдел:",
                    "reply_markup": build_keyboard(departments, "otdel")
                },
            )
            return {"ok": True}

        # ===== СУММА =====
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

        # ===== КОММЕНТАРИЙ =====
        if chat_id in temp_storage and "summa" in temp_storage[chat_id]:
            comment = text
            row = temp_storage[chat_id]

            values = [[
                row["schet"],
                row["operacia"],
                row.get("date", ""),
                row["otdel"],
                row["state"],
                row["summa"],
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
                    "text": "✅ Операция сохранена.",
                },
            )

            del temp_storage[chat_id]
            return {"ok": True}

        # ===== START =====
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