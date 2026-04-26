import os, httpx
from dotenv import load_dotenv

load_dotenv()

GMAIL_URL = os.getenv("GMAIL_API_URL", "")
GMAIL_TOKEN = os.getenv("GMAIL_API_TOKEN", "")
DEFAULT_EMAILS = ["vet_batyam@yahoo.com", "vetrinarbatyam@gmail.com"]


def send_meal_email(to_emails: list[str], subject: str, html_body: str) -> dict:
    if not GMAIL_URL or not GMAIL_TOKEN:
        return {"error": "Gmail not configured"}

    results = []
    for email in to_emails:
        try:
            resp = httpx.post(
                GMAIL_URL,
                json={
                    "action": "send",
                    "token": GMAIL_TOKEN,
                    "to": email,
                    "subject": subject,
                    "html": html_body,
                },
                timeout=30,
            )
            results.append({"email": email, "status": resp.status_code, "body": resp.text[:200]})
        except Exception as e:
            results.append({"email": email, "error": str(e)})
    return {"sent": results}
