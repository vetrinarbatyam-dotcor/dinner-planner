import os, httpx
from dotenv import load_dotenv

load_dotenv()

GIL_INSTANCE = os.getenv("GIL_WHATSAPP_INSTANCE", "7107590522")
GIL_TOKEN = os.getenv("GIL_WHATSAPP_TOKEN", "")
BASE_URL = "https://api.green-api.com"


def _send_text(instance: str, token: str, phone: str, message: str) -> dict:
    phone_id = phone.replace("+", "").replace("-", "").replace(" ", "")
    if not phone_id.startswith("972"):
        if phone_id.startswith("0"):
            phone_id = "972" + phone_id[1:]
        else:
            phone_id = "972" + phone_id
    chat_id = f"{phone_id}@c.us"
    url = f"{BASE_URL}/waInstance{instance}/sendMessage/{token}"
    resp = httpx.post(url, json={"chatId": chat_id, "message": message}, timeout=30)
    return resp.json()


def send_meal_to_whatsapp(phone: str, meal_summary: str, recipient_name: str = "") -> dict:
    instance = GIL_INSTANCE
    token = GIL_TOKEN
    if not token:
        return {"error": "WhatsApp token not configured"}

    greeting = f"שלום {recipient_name}! " if recipient_name else ""
    message = f"""{greeting}🍽️ *ארוחת הערב שתכננת*

{meal_summary}

_נשלח מ-מתכנן הארוחה_ 🤖"""

    return _send_text(instance, token, phone, message)
