# -*- coding: utf-8 -*-
""" /start — роль-aware приветствие + кнопка Mini App (01_/10_). """

from __future__ import annotations

import logging
import os

import httpx
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)

logger = logging.getLogger("qpremium.bot.start")
router = Router(name="start")


def _api_base() -> str:
    return (os.getenv("PUBLIC_BASE_URL") or "http://localhost:8000").rstrip("/")


def _miniapp_url() -> str:
    path = (os.getenv("MINIAPP_URL_FILE") or "").strip()
    if path and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                val = f.read().strip()
            if val:
                return val
        except OSError:
            pass
    return (os.getenv("MINIAPP_URL") or f"{_api_base()}/app/").strip()


def _webapp_keyboard() -> InlineKeyboardMarkup | None:
    url = _miniapp_url()
    if not url.startswith("https://"):
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть Q Premium", web_app=WebAppInfo(url=url))]
        ]
    )


async def _sync_menu_button(message: Message, url: str) -> None:
    """Актуальный URL на кнопке Q Premium слева внизу в Telegram."""
    if not url.startswith("https://") or not message.bot:
        return
    try:
        await message.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Q Premium", web_app=WebAppInfo(url=url))
        )
        if message.chat:
            await message.bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(text="Q Premium", web_app=WebAppInfo(url=url)),
            )
    except Exception:  # noqa: BLE001
        logger.exception("set_chat_menu_button failed")


def _resolve_role(telegram_id: int) -> str:
    api = _api_base()
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{api}/api/v1/auth/bot-resolve",
                headers={"Authorization": f"Bot {token}"},
                json={"telegram_id": telegram_id},
            )
            if resp.status_code == 200:
                return str(resp.json().get("role") or "NONE")
    except Exception:  # noqa: BLE001
        logger.exception("role resolve failed tg=%s", telegram_id)
    return "NONE"


def _fetch_welcome_settings() -> dict:
    api = _api_base()
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{api}/api/v1/bot/welcome")
            if resp.status_code == 200:
                return resp.json()
    except Exception:  # noqa: BLE001
        logger.exception("welcome settings fetch failed")
    return {}


def _role_suffix(role: str) -> str:
    if role == "ADMIN":
        return "\n\nВы вошли как администратор."
    if role == "STORE":
        return "\n\nВы вошли как кассир."
    return ""


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        return
    role = _resolve_role(message.from_user.id)
    url = _miniapp_url()
    kb = _webapp_keyboard()
    await _sync_menu_button(message, url)

    welcome = _fetch_welcome_settings()
    text = (welcome.get("text") or "").strip() or (
        "Добро пожаловать в Q Premium — программу лояльности магазинов одежды."
    )
    text = text + _role_suffix(role)
    photo_url = (welcome.get("photo_url") or "").strip()

    # Ссылка только в кнопках («Открыть Q Premium» и меню Q Premium), не в тексте
    if not url.startswith("https://"):
        text += (
            "\n\n<i>Mini App пока недоступен: нужен HTTPS-туннель. "
            "После запуска туннеля нажмите /start ещё раз.</i>"
        )

    if photo_url:
        try:
            with httpx.Client(timeout=20.0) as client:
                img = client.get(photo_url)
                img.raise_for_status()
                photo = BufferedInputFile(img.content, filename="welcome.jpg")
            await message.answer_photo(photo, caption=text[:1024], reply_markup=kb)
            return
        except Exception:  # noqa: BLE001
            logger.exception("welcome photo send failed, fallback to text")

    await message.answer(text, reply_markup=kb)


@router.message(F.text)
async def fallback_text(message: Message) -> None:
    await message.answer(
        "Используйте /start или кнопку Mini App. Операции баллов — только в приложении."
    )
