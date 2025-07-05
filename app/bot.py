import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from app.database import database
from app.languages import LANGUAGES
from app.spaces_client import list_today_slots, load_play_url, load_slot_metadata
from sqlalchemy.dialects.postgresql import insert
from datetime import date
from .config import settings
from .models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory cache for Telegram file_ids
FILE_ID_CACHE: dict[str, str] = {}


async def register_user(user_data):
    stmt = insert(User).values(
        chat_id=user_data.id,
        username=user_data.username
    ).on_conflict_do_nothing(index_elements=['chat_id'])
    await database.execute(stmt)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await register_user(user)
    # Build language selection buttons
    keyboard = [
        [InlineKeyboardButton(f"{LANGUAGES[lang]['flag']} {lang}", callback_data=f"lang|{lang}")]
        for lang in LANGUAGES.keys()
    ]
    text = LANGUAGES['AZ']['welcome'].format(first_name=user.first_name)
    await update.message.reply_markdown(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 1) pull lang & template
    _, lang = query.data.split("|", 1)
    context.user_data['lang'] = lang
    tpl = LANGUAGES[lang]

    # 2) build your header
    today = date.today().strftime("%d.%m.%Y")
    header_text = tpl["top_slots"].format(today=today) + "\n\n" + tpl["description"]

    # 3) raw slots + metadata ordering
    raw_slots = list_today_slots(lang)
    metadata_map = load_slot_metadata(lang)

    # preserve only those that exist in raw_slots, in metadata.json order:
    ordered_slots = [
        next((s for s in raw_slots if s["name"] == name), None)
        for name in metadata_map.keys()
    ]
    slot_items = [s for s in ordered_slots if s]

    if not slot_items:
        return await query.edit_message_text(tpl["no_slots"], parse_mode="Markdown")

    # 4) build buttons in that order
    keyboard = [
        [InlineKeyboardButton(item["name"], callback_data=f"slot|{item['name']}")]
        for item in slot_items
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_language")])

    await query.edit_message_text(
        text=header_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def back_to_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Simulate /start again, but use the CallbackQuery
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton(f"{LANGUAGES[lang]['flag']} {lang}", callback_data=f"lang|{lang}")]
        for lang in LANGUAGES.keys()
    ]
    text = LANGUAGES['AZ']['welcome'].format(first_name=user.first_name)
    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "AZ")
    tpl = LANGUAGES[lang]

    # 1) re-load slots & metadata map
    raw_slots = list_today_slots(lang)
    metadata_map = load_slot_metadata(lang)

    # 2) re-derive the same ordered list
    ordered = [
        next((s for s in raw_slots if s["name"] == name), None)
        for name in metadata_map.keys()
    ]
    slots = [s for s in ordered if s]

    # 3) pick the one the user tapped
    slot_name = query.data.split("|", 1)[1]
    slot = next((s for s in slots if s["name"] == slot_name), None)
    if not slot:
        return await query.message.reply_text(tpl["slot_not_found"], parse_mode="Markdown")

    # 4) find its position & medal
    pos = [s["name"] for s in slots].index(slot_name)
    medals = ["🥇", "🥈", "🥉"]
    prefix = medals[pos] if pos < 3 else f"{pos + 1}."

    # 5) get its metadata fields
    meta = metadata_map.get(slot_name, {})
    caption = (
        f"{slot_name}\n"
        f"└🎮 Sağlayıcı: {meta.get('provider', '—')}\n"
        f"- Əsas RTP: {meta.get('base_rtp', '—')}%\n"
        f"⚡️ Cari RTP: <b>{meta.get('instant_rtp', '—')}%</b>\n"
        f"Həftəlik RTP: {meta.get('weekly_rtp', '—')}%"
    )

    # 6) buttons & send
    play_url = load_play_url()
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(tpl["check_in"], url=play_url),
        InlineKeyboardButton(tpl["back_slots"], callback_data="back_to_slots"),
    ]])

    msg = await query.message.reply_photo(
        photo=slot["image"],
        caption=caption,
        parse_mode="HTML",
        reply_markup=kb,
    )

    # 7) cache file_id as before
    url = slot["image"]
    if url not in FILE_ID_CACHE:
        FILE_ID_CACHE[url] = msg.photo[-1].file_id


async def back_to_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get('lang', 'AZ')
    tpl = LANGUAGES[lang]
    today = date.today().strftime("%d.%m.%Y")
    header_text = tpl["top_slots"].format(today=today) + "\n\n" + tpl["description"]

    # 1) get the “flat” slots
    raw_slots = list_today_slots(lang)
    slot_map = {s["name"]: s for s in raw_slots}

    # 2) load your metadata.json (keys are in the order you declared them)
    metadata_map = load_slot_metadata(lang)
    ordered_names = [name for name in metadata_map.keys() if name in slot_map]

    # 3) now build buttons in that exact sequence
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"slot|{name}")]
        for name in ordered_names
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_language")])

    # 4) edit the existing message (or reply if you prefer)
    await query.edit_message_text(
        text=header_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def create_bot():
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(choose_language, pattern=r'^lang\|'))
    application.add_handler(CallbackQueryHandler(choose_slot, pattern=r'^slot\|'))
    application.add_handler(CallbackQueryHandler(back_to_language, pattern=r'^back_to_language$'))
    application.add_handler(CallbackQueryHandler(back_to_slots, pattern=r'^back_to_slots$'))
    return application
