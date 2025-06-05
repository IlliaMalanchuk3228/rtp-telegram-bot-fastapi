# app/languages.py

from datetime import date


def today_str() -> str:
    """Returns today in YYYYMMDD for filename stamping."""
    return date.today().strftime("%Y%m%d")


LANGUAGES = {
    "AZERBAIDJANI": {
        "flag": "🇦🇿",
        "welcome": (
            "👋 *Xoş gəlmisiniz, {first_name}!*\n\n"
            "Abunə olduğunuz üçün təşəkkür edirəm.\n\n"
            "Xahiş edirəm dili seçin:"
        ),
        "top_slots": "🎰 *Bu Günün Ən Yaxşı Slotları* – {today}",
        "description": "Aşağıdan bu günün ən sevilən slotlarını seçin və dərhal oynayın!",
        "pick_prompt": "Slot seçin:",
        "check_in": "📲 Oyna",
    },
    "UZBEK": {
        "flag": "🇺🇿",
        "welcome": (
            "👋 *Хуш омадед, {first_name}!*\n\n"
            "Ба обуна шуданатон ташаккур.\n\n"
            "Лутфан забонро интихоб кунед:"
        ),
        "top_slots": "🎰 *Беҳтарин Слотҳои Имрӯз* – {today}",
        "description": "Аз зери тугмаҳо беҳтарин слотҳои имрӯзро интихоб кунед ва фавран бозӣ кунед!",
        "pick_prompt": "Слотро интихоб кунед:",
        "check_in": "📲 Бозӣ кунед",
    },
}
