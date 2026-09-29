# -*- coding: utf-8 -*-
"""Q Premium Telegram bot (aiogram): entrypoint, Mini App, no Engine math."""

from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeChat
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
    dp.startup.register(_set_commands)

    logger.info("Q Premium bot starting (polling)")
    asyncio.run(dp.start_polling(bot))


async def _set_commands(bot: Bot) -> None:
    common = [BotCommand(command="start", description="Открыть Q Premium")]
    try:
        await bot.set_my_commands(common)
    except Exception:  # noqa: BLE001
        logger.exception("set_my_commands failed")
        return
    raw = (os.getenv("ADMIN_TELEGRAM_ID") or "").strip()
    if not raw.isdigit():
        return
    try:
        await bot.set_my_commands(
            common
            + [
                BotCommand(command="clients", description="Excel со всеми клиентами"),
                BotCommand(command="backup", description="Резервная копия базы"),
            ],
            scope=BotCommandScopeChat(chat_id=int(raw)),
        )
    except Exception:  # noqa: BLE001
        logger.exception("admin command menu failed tg=%s", raw)


async def _idle() -> None:
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    main()
