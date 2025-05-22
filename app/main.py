import asyncio
from telegram import Update
from fastapi import FastAPI, Request, Response
from app.bot import create_bot, settings
from app.database import database
from alembic.config import Config
from alembic import command

app = FastAPI()
bot = create_bot()


@app.on_event("startup")
async def startup():
    # Connect database
    await database.connect()

    # 2) run Alembic migrations at runtime (inside the VPC)
    def _migrate():
        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))
        command.upgrade(cfg, "head")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _migrate)

    # Initialize bot and set webhook
    await bot.initialize()
    await bot.bot.set_webhook(url=settings.WEBHOOK_URL)

    # Optional: print webhook info for debugging
    info = await bot.bot.get_webhook_info()
    print("DEBUG: Webhook info:", info)


@app.on_event("shutdown")
async def shutdown():
    await bot.bot.delete_webhook()
    await bot.shutdown()
    await database.disconnect()


@app.get("/")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    update_json = await request.json()
    # Convert the JSON payload to a proper Update object
    print("DEBUG: Received update JSON:", update_json)  # Log the raw JSON
    try:
        update = Update.de_json(update_json, bot.bot)
        print("DEBUG: Parsed update:", update)  # Log the parsed Update object
        await bot.process_update(update)
    except Exception as e:
        print("DEBUG: Exception in processing update:", e)
    return Response(status_code=200)
