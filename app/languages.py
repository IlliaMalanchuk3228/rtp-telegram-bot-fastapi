# app/languages.py

from datetime import date


def today_str() -> str:
    """Returns today in YYYYMMDD for filename stamping."""
    return date.today().strftime("%Y%m%d")


LANGUAGES = {
    "AZ": {
        "flag": "🇦🇿",
        "welcome": (
            "👋 *Xoş gəlmisiniz, {first_name}!*\n\n"
            "Abunə olduğunuz üçün təşəkkür edirəm.\n\n"
            "Xahiş edirəm dili seç:"
        ),
        "top_slots": "🎰 *Bu Günün Ən Yüksək RTP Slotları* – {today}",
        "description": "Aşağıdan bu günün ən sevilən slot seç və oyna!",
        "pick_prompt": "Slot seç:",
        "check_in": "📲 Oynamaq üçün bas",
        "back_slots": "⬅️ Slotlara qayıtmaq",
        "no_slots": "Üzr istəyirəm, bu gün üçün slotlar yoxdur.",
        "slot_not_found":  "Üzr istəyirəm, bu slot tapılmadı."
    },
        # "UZ": {
        #     "flag": "🇺🇿",
        #     "welcome": (
        #         "👋 *Хуш омадед, {first_name}!*\n\n"
        #         "Ба обуна шуданатон ташаккур.\n\n"
        #         "Лутфан забонро интихоб кунед:"
        #     ),
        #     "top_slots": "🎰 *Беҳтарин Слотҳои Имрӯз* – {today}",
        #     "description": "Аз зери тугмаҳо беҳтарин слотҳои имрӯзро интихоб кунед ва фавран бозӣ кунед!",
        #     "pick_prompt": "Слотро интихоб кунед:",
        #     "check_in": "📲 Saytda o‘ynang",
        #     "back_slots": "⬅️ Slotlarga qayting",
        #     "no_slots": "Kechirasiz, bugun uchun bo‘sh joylar mavjud emas.",
        #     "slot_not_found":  "Kechirasiz, bu slot topilmadi."
        # },
}
