import os, json, re
from google import genai
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

BUDGET_MAP = {"cheap": "זול (עד ₪30 למנה)", "medium": "בינוני (₪30-₪80 למנה)", "expensive": "יקר (₪80+ למנה)"}
DIFFICULTY_MAP = {"easy": "קל", "medium": "בינוני", "hard": "מאתגר"}
STYLE_MAP = {
    "daily": "יומיומי", "shabbat": "שבתי", "festive": "חגיגי",
    "fancy": "מפואר", "holiday": "חג", "birthday": "יום הולדת", "business": "עסקי"
}


def build_source_description(sources: dict) -> str:
    parts = []
    if sources.get("social"):
        parts.append(f"רשתות חברתיות: {', '.join(sources['social'])}")
    if sources.get("israeli_chefs"):
        parts.append(f"שפים ישראלים: {', '.join(sources['israeli_chefs'])}")
    if sources.get("international_chefs"):
        parts.append(f"שפים בינלאומיים: {', '.join(sources['international_chefs'])}")
    if sources.get("hebrew_sites"):
        parts.append(f"אתרים בעברית: {', '.join(sources['hebrew_sites'])}")
    return " | ".join(parts) if parts else "כל המקורות"


def search_recipes(
    course_type: str,
    course_name: str,
    n_options: int,
    participants: int,
    style: str,
    difficulty: str,
    budget: str,
    sources: dict,
    occasion: str = "",
) -> list[dict]:
    source_desc = build_source_description(sources)
    budget_heb = BUDGET_MAP.get(budget, budget)
    difficulty_heb = DIFFICULTY_MAP.get(difficulty, difficulty)
    style_heb = STYLE_MAP.get(style, style)

    prompt = f"""אתה מומחה קולינרי ישראלי. תפקידך להמליץ על מתכונים אמיתיים לארוחת ערב.

פרטי הארוחה:
- מנה: {course_name}
- מספר סועדים: {participants}
- סגנון: {style_heb}
- אירוע: {occasion or style_heb}
- קושי: {difficulty_heb}
- תקציב: {budget_heb}
- מקורות מועדפים: {source_desc}

תן לי בדיוק {n_options} מתכונים שונים ומגוונים לـ{course_name}.

החזר JSON תקין בלבד (ללא markdown, ללא ```, ללא שום טקסט לפני או אחרי):
[
  {{
    "name": "שם המנה בעברית",
    "chef_or_source": "שם השף או המקור",
    "source_url": "URL אמיתי למתכון",
    "prep_time": "זמן הכנה (לדוגמה: 45 דקות)",
    "difficulty": "קל/בינוני/מאתגר",
    "cost_per_person": 45,
    "main_ingredients": ["מרכיב1", "מרכיב2", "מרכיב3"],
    "all_ingredients": [
      {{"name": "שם המרכיב", "quantity": "כמות ל-{participants} סועדים", "unit": "יחידה", "category": "ירקות/בשר/דגים/חלב/יבשים/תבלינים/שמנים/אחר"}}
    ],
    "short_description": "תיאור קצר ומפתה (2 משפטים)",
    "cooking_steps_summary": "3-4 שלבים עיקריים"
  }}
]"""

    client = get_client()
    resp = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt,
    )
    raw = resp.text.strip()

    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()

    try:
        recipes = json.loads(raw)
        return recipes if isinstance(recipes, list) else []
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        return []
