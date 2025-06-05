import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from app.database import database
from app.languages import LANGUAGES
from app.spaces_client import list_today_slots, load_play_url
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
    text = LANGUAGES['AZERBAIDJANI']['welcome'].format(first_name=user.first_name)
    await update.message.reply_markdown(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, lang = query.data.split("|", 1)
    context.user_data['lang'] = lang
    tpl = LANGUAGES[lang]

    # compute today once
    today = date.today().strftime("%d.%m.%Y")
    # format the header
    header_text = tpl["top_slots"].format(today=today) + "\n\n" + tpl["description"]

    # List today’s slot files from Spaces
    slot_items = list_today_slots(lang)
    if not slot_items:
        await query.edit_message_text("Üzgünüm, bugün için slotlar mevcut değil.")
        return

    # Build slot buttons
    keyboard = [
        [InlineKeyboardButton(item['name'], callback_data=f"slot|{item['name']}")]
        for item in slot_items
    ]

    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_language")])

    await query.edit_message_text(
        text=header_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
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
    text = LANGUAGES['AZERBAIDJANI']['welcome'].format(first_name=user.first_name)
    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    slot_name = query.data.split("|", 1)[1]
    lang = context.user_data.get('lang', 'AZERBAIDJANI')

    # Re-list today’s slots and find the selected one
    slots = list_today_slots(lang)
    slot = next((s for s in slots if s['name'] == slot_name), None)
    if not slot:
        await query.message.reply_text("Bu slot bulunamadı.")
        return

    # fetch the one, shared play-url
    play_url = load_play_url()

    # button with that URL
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("▶️ Try on website", url=play_url),
        InlineKeyboardButton("⬅️ Back to slots", callback_data="back_to_slots")
    ]])

    msg = await query.message.reply_photo(
        photo=slot["image"],
        caption=f"*{slot_name}*",
        parse_mode="Markdown",
        reply_markup=kb
    )

    # cache Telegram file_id as before
    url = slot["image"]
    if url not in FILE_ID_CACHE:
        FILE_ID_CACHE[url] = msg.photo[-1].file_id


async def back_to_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'AZERBAIDJANI')
    tpl = LANGUAGES[lang]
    today = date.today().strftime("%d.%m.%Y")
    header_text = tpl["top_slots"].format(today=today) + "\n\n" + tpl["description"]
    slot_items = list_today_slots(lang)
    keyboard = [
        [InlineKeyboardButton(item['name'], callback_data=f"slot|{item['name']}")]
        for item in slot_items
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_language")])

    # **Send a new message with slots**
    await query.message.reply_text(
        text=header_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    try:
        await query.message.delete()
    except Exception as e:
        pass  # If can't delete, just ignore

def create_bot():
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(choose_language, pattern=r'^lang\|'))
    application.add_handler(CallbackQueryHandler(choose_slot, pattern=r'^slot\|'))
    application.add_handler(CallbackQueryHandler(back_to_language, pattern=r'^back_to_language$'))
    application.add_handler(CallbackQueryHandler(back_to_slots, pattern=r'^back_to_slots$'))
    return application
