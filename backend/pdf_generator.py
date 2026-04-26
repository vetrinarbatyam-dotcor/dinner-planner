import io
from jinja2 import Template

HTML_TEMPLATE = """<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: 'Arial', sans-serif; direction: rtl; margin: 30px; color: #222; }
  h1 { color: #b5451b; border-bottom: 2px solid #b5451b; padding-bottom: 8px; }
  h2 { color: #7c4a00; margin-top: 28px; }
  h3 { color: #444; margin: 16px 0 6px; }
  .course-block { background: #fdf6ee; border-radius: 10px; padding: 16px; margin: 16px 0; border-right: 4px solid #b5451b; }
  .tag { display: inline-block; background: #ffe0c0; color: #7c4a00; border-radius: 12px; padding: 2px 10px; font-size: 12px; margin: 2px; }
  .ingredients-section { margin-top: 30px; }
  .cat-block { margin: 14px 0; }
  .cat-title { font-weight: bold; color: #555; border-bottom: 1px dashed #ccc; padding-bottom: 4px; margin-bottom: 6px; }
  ul { margin: 4px 0; padding-right: 18px; }
  li { margin: 3px 0; }
  .footer { margin-top: 40px; color: #888; font-size: 12px; text-align: center; }
</style>
</head>
<body>
<h1>🍽️ ארוחת הערב שלי</h1>
<p><strong>{{ params.participants }} סועדים</strong> &bull; {{ params.style_heb }} &bull; {{ params.occasion }}</p>

<h2>📋 תפריט</h2>
{% for course in courses %}
<div class="course-block">
  <h3>{{ course.emoji }} {{ course.course_name }}</h3>
  <strong>{{ course.recipe.name }}</strong>
  {% if course.recipe.chef_or_source %}<span class="tag">{{ course.recipe.chef_or_source }}</span>{% endif %}
  <span class="tag">⏱ {{ course.recipe.prep_time }}</span>
  <span class="tag">💰 ₪{{ course.recipe.cost_per_person }} למנה</span>
  <p>{{ course.recipe.short_description }}</p>
  <em>{{ course.recipe.cooking_steps_summary }}</em>
  {% if course.recipe.source_url %}<p><small>מקור: {{ course.recipe.source_url }}</small></p>{% endif %}
</div>
{% endfor %}

<div class="ingredients-section">
<h2>🛒 רשימת קנייה</h2>
{% for cat in ingredients %}
<div class="cat-block">
  <div class="cat-title">{{ cat.emoji }} {{ cat.category }}</div>
  <ul>
  {% for item in cat.items %}
    <li>{{ item.name }} — {{ item.quantity }} {{ item.unit }} <small>({{ item.from_dish }})</small></li>
  {% endfor %}
  </ul>
</div>
{% endfor %}
</div>

<div class="footer">נוצר על ידי מתכנן הארוחה 🤖 | {{ date }}</div>
</body>
</html>"""


def generate_pdf_html(courses: list, ingredients: list, params: dict, date: str) -> bytes:
    try:
        from weasyprint import HTML as WP
        html_str = Template(HTML_TEMPLATE).render(
            courses=courses, ingredients=ingredients, params=params, date=date
        )
        return WP(string=html_str).write_pdf()
    except Exception:
        html_str = Template(HTML_TEMPLATE).render(
            courses=courses, ingredients=ingredients, params=params, date=date
        )
        return html_str.encode("utf-8")


def generate_html_string(courses: list, ingredients: list, params: dict, date: str) -> str:
    return Template(HTML_TEMPLATE).render(
        courses=courses, ingredients=ingredients, params=params, date=date
    )
