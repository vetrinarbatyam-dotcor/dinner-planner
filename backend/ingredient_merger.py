from collections import defaultdict

CATEGORY_ORDER = ["בשר", "דגים", "עוף", "ירקות", "פירות", "חלב", "ביצים", "יבשים", "תבלינים", "שמנים", "אחר"]
CATEGORY_EMOJI = {
    "בשר": "🥩", "דגים": "🐟", "עוף": "🍗", "ירקות": "🥦",
    "פירות": "🍋", "חלב": "🧀", "ביצים": "🥚", "יבשים": "🫙",
    "תבלינים": "🌿", "שמנים": "🫒", "אחר": "📦"
}


def merge_ingredients(selected_recipes: list[dict]) -> dict:
    by_category = defaultdict(list)
    for recipe in selected_recipes:
        for ing in recipe.get("all_ingredients", []):
            cat = ing.get("category", "אחר")
            normalized_cat = _normalize_category(cat)
            by_category[normalized_cat].append({
                "name": ing.get("name", ""),
                "quantity": ing.get("quantity", ""),
                "unit": ing.get("unit", ""),
                "from_dish": recipe.get("name", ""),
            })

    result = []
    for cat in CATEGORY_ORDER:
        items = by_category.get(cat, [])
        if items:
            result.append({
                "category": cat,
                "emoji": CATEGORY_EMOJI.get(cat, "📦"),
                "items": items,
            })
    remaining = set(by_category.keys()) - set(CATEGORY_ORDER)
    for cat in remaining:
        result.append({
            "category": cat,
            "emoji": "📦",
            "items": by_category[cat],
        })
    return result


def _normalize_category(cat: str) -> str:
    cat_lower = cat.lower()
    if any(w in cat_lower for w in ["בשר", "meat", "lamb", "beef"]):
        return "בשר"
    if any(w in cat_lower for w in ["דג", "fish", "seafood", "ים"]):
        return "דגים"
    if any(w in cat_lower for w in ["עוף", "chicken", "turkey"]):
        return "עוף"
    if any(w in cat_lower for w in ["ירק", "vegetable", "עגבני", "מלפפ", "גזר", "בצל", "שום"]):
        return "ירקות"
    if any(w in cat_lower for w in ["פרי", "fruit", "תפוח", "לימון", "תפוז"]):
        return "פירות"
    if any(w in cat_lower for w in ["חלב", "גבינ", "dairy", "שמנת", "יוגורט"]):
        return "חלב"
    if any(w in cat_lower for w in ["ביצ", "egg"]):
        return "ביצים"
    if any(w in cat_lower for w in ["יבש", "קמח", "אורז", "פסטה", "עדש", "שעועי", "גריס", "שמיר"]):
        return "יבשים"
    if any(w in cat_lower for w in ["תבל", "spice", "מלח", "פלפל", "כורכ", "פפריק"]):
        return "תבלינים"
    if any(w in cat_lower for w in ["שמן", "oil", "חמאה", "butter"]):
        return "שמנים"
    return "אחר"
