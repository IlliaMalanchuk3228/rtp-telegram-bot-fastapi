import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from app.database import database
from sqlalchemy.dialects.postgresql import insert
from .models import User
from pydantic import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    WEBHOOK_URL: str

    class Config:
        env_file = ".env"


settings = Settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_bot():
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    return application


async def register_user(user_data):
    stmt = insert(User).values(
        chat_id=user_data.id,
        username=user_data.username
    ).on_conflict_do_nothing(index_elements=['chat_id'])
    await database.execute(stmt)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: /start command triggered for user:", update.effective_user)
    await register_user(update.effective_user)
    await update.message.reply_text("You've been subscribed successfully!")
