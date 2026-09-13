# -*- coding: utf-8 -*-
"""Q Premium Telegram bot (aiogram) — entry, Mini App, no Engine math (18_)."""

from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from bot.handlers import start

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qpremium.bot")


def main() -> None:
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        logger.warning(
            "TELEGRAM_BOT_TOKEN пуст — бот в режиме ожидания (compose не падает). "
            "Укажите токен в .env и перезапустите сервис bot."
        )
        asyncio.run(_idle())
        return

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(start.router)

    logger.info("Q Premium bot starting (polling)")
    asyncio.run(dp.start_polling(bot))


async def _idle() -> None:
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    main()
