# github_runner.py
import os
import logging
import asyncio
from telegram import Bot
from checker import check_and_notify

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("BOT_TOKEN/CHAT_ID не переданы через переменные окружения")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

async def run_once():
    bot = Bot(BOT_TOKEN)
    await check_and_notify(bot, CHAT_ID)

if __name__ == "__main__":
    asyncio.run(run_once())