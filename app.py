import os
from fastapi import FastAPI, Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()

# ====== НАСТРОЙКИ ======
SPREADSHEET_ID = "ВСТАВЬ_ID_ТАБЛИЦЫ"
SHEET_NAME = "Лист1"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

import json
import os

creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])

credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=SCOPES,
)

service = build("sheets", "v4", credentials=credentials)


@app.post("/")
async def webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    text = data["message"].get("text", "")
    user = data["message"]["from"].get("username", "")
    update_id = data.get("update_id")

    values = [[update_id, user, text]]

    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=SHEET_NAME,
        valueInputOption="RAW",
        body={"values": values},
    ).execute()

    return {"ok": True}