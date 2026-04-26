import os, json
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from chefs_list import ISRAELI_CHEFS, INTERNATIONAL_CHEFS, HEBREW_SITES, SOCIAL_SOURCES, COURSE_TYPES
from recipe_search import search_recipes
from ingredient_merger import merge_ingredients
from whatsapp_sender import send_meal_to_whatsapp
from email_sender import send_meal_email, DEFAULT_EMAILS
from pdf_generator import generate_pdf_html, generate_html_string

load_dotenv()

app = FastAPI(title="מתכנן ארוחת ערב")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STYLE_MAP = {
    "daily": "יומיומי", "shabbat": "שבתי", "festive": "חגיגי",
    "fancy": "מפואר", "holiday": "חג", "birthday": "יום הולדת", "business": "עסקי"
}

# ──── Pydantic models ────────────────────────────────────────────────

class CourseRequest(BaseModel):
    course_type: str
    course_name: str
    n_options: int = 3

class SearchRequest(BaseModel):
    participants: int
    style: str
    difficulty: str
    budget: str
    occasion: str = ""
    cuisines: list[str] = []
    diet: str = ""
    custom_theme: str = ""
    sources: dict
    courses: list[CourseRequest]

class SelectedRecipe(BaseModel):
    course_type: str
    course_name: str
    emoji: str
    recipe: dict

class CompileRequest(BaseModel):
    participants: int
    style: str
    occasion: str = ""
    selected: list[SelectedRecipe]

class SendRequest(BaseModel):
    compile_data: CompileRequest
    send_email: bool = False
    email_to: list[str] = []
    send_whatsapp: bool = False
    whatsapp_phone: str = ""
    whatsapp_name: str = ""
    generate_pdf: bool = False

# ──── Routes ────────────────────────────────────────────────────────

@app.get("/api/config")
def get_config():
    return {
        "israeli_chefs": ISRAELI_CHEFS,
        "international_chefs": INTERNATIONAL_CHEFS,
        "hebrew_sites": HEBREW_SITES,
        "social_sources": SOCIAL_SOURCES,
        "course_types": COURSE_TYPES,
    }

@app.post("/api/search-recipes")
async def api_search_recipes(req: SearchRequest):
    results = {}
    for course in req.courses:
        recipes = search_recipes(
            course_type=course.course_type,
            course_name=course.course_name,
            n_options=course.n_options,
            participants=req.participants,
            style=req.style,
            difficulty=req.difficulty,
            budget=req.budget,
            sources=req.sources,
            occasion=req.occasion,
            cuisines=req.cuisines,
            diet=req.diet,
            custom_theme=req.custom_theme,
        )
        results[course.course_type] = recipes
    return {"results": results}

@app.post("/api/compile-meal")
async def api_compile_meal(req: CompileRequest):
    recipes = [s.recipe for s in req.selected]
    ingredients = merge_ingredients(recipes)
    style_heb = STYLE_MAP.get(req.style, req.style)
    return {
        "courses": [s.dict() for s in req.selected],
        "ingredients": ingredients,
        "params": {
            "participants": req.participants,
            "style": req.style,
            "style_heb": style_heb,
            "occasion": req.occasion,
        },
    }

@app.post("/api/send")
async def api_send(req: SendRequest):
    compile_req = req.compile_data
    recipes = [s.recipe for s in compile_req.selected]
    ingredients = merge_ingredients(recipes)
    style_heb = STYLE_MAP.get(compile_req.style, compile_req.style)
    params = {
        "participants": compile_req.participants,
        "style": compile_req.style,
        "style_heb": style_heb,
        "occasion": compile_req.occasion,
    }
    today = date.today().strftime("%d/%m/%Y")
    courses_list = [s.dict() for s in compile_req.selected]
    results = {}

    if req.send_email:
        html = generate_html_string(courses_list, ingredients, params, today)
        subject = f"🍽️ ארוחת הערב שלך — {today}"
        targets = req.email_to if req.email_to else DEFAULT_EMAILS
        results["email"] = send_meal_email(targets, subject, html)

    if req.send_whatsapp:
        lines = ["🍽️ *התפריט שלך:*\n"]
        for s in compile_req.selected:
            lines.append(f"{s.emoji} *{s.course_name}*: {s.recipe.get('name','')}")
        lines.append("\n🛒 *רשימת קנייה ראשית:*")
        for cat in ingredients:
            lines.append(f"\n{cat['emoji']} *{cat['category']}*")
            for item in cat["items"][:5]:
                lines.append(f"  • {item['name']} — {item['quantity']} {item['unit']}")
        summary = "\n".join(lines)
        phone = req.whatsapp_phone or "0543123419"
        results["whatsapp"] = send_meal_to_whatsapp(phone, summary, req.whatsapp_name)

    return results

@app.post("/api/generate-pdf")
async def api_generate_pdf(req: CompileRequest):
    recipes = [s.recipe for s in req.selected]
    ingredients = merge_ingredients(recipes)
    style_heb = STYLE_MAP.get(req.style, req.style)
    params = {
        "participants": req.participants,
        "style": req.style,
        "style_heb": style_heb,
        "occasion": req.occasion,
    }
    today = date.today().strftime("%d/%m/%Y")
    courses_list = [s.dict() for s in req.selected]
    pdf_bytes = generate_pdf_html(courses_list, ingredients, params, today)

    if pdf_bytes[:4] == b"%PDF":
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": "attachment; filename=dinner-plan.pdf"})
    return Response(content=pdf_bytes, media_type="text/html; charset=utf-8")

# ──── Serve frontend ─────────────────────────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3006, reload=False)
