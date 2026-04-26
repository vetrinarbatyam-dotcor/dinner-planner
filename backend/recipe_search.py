import os, json, re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

עבור כל מתכון תחזיר JSON תקין בלבד (ללא markdown, ללא ```):
[
  {{
    "name": "שם המנה בעברית",
    "name_en": "Dish name in English",
    "chef_or_source": "שם השף או המקור (אתר/פרסום)",
    "source_url": "כתובת URL למתכון או לדף המקור (אמיתי ומדויק ככל האפשר)",
    "prep_time": "זמן הכנה + בישול (לדוגמה: 45 דקות)",
    "difficulty": "קל/בינוני/מאתגר",
    "cost_per_person": "עלות משוערת למנה בשקלים (מספר בלבד)",
    "main_ingredients": ["מרכיב1", "מרכיב2", "מרכיב3"],
    "all_ingredients": [
      {{"name": "שם המרכיב", "quantity": "כמות ל-{participants} סועדים", "unit": "יחידת מידה", "category": "ירקות/בשר/דגים/חלב/יבשים/תבלינים/שמנים/אחר"}}
    ],
    "short_description": "תיאור קצר ומפתה של המנה (2 משפטים)",
    "cooking_steps_summary": "3-4 שלבי בישול עיקריים בתמצית"
  }}
]

חשוב:
- הצע מגוון אמיתי — לא כולם אותו סגנון
- התאם לתקציב ולרמת הקושי שנבחרו
- כמויות המרכיבים — ל-{participants} סועדים בדיוק
- כתובות URL — נסה להיות מדויק לאתרים אמיתיים (mako.co.il, walla.co.il, jamieoliver.com וכד')
- החזר JSON תקין בלבד, ללא שום טקסט נוסף"""

    model = genai.GenerativeModel("gemini-2.0-flash")
    resp = model.generate_content(prompt)
    raw = resp.text.strip()

    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()

    try:
        recipes = json.loads(raw)
        return recipes if isinstance(recipes, list) else []
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
