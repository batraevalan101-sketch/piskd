from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from keyboards.kb import settings_kb, main_menu_kb
from services.factory import PROVIDER_LABELS
from utils.storage import get_settings, set_setting

router = Router()


@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def cmd_settings(msg: Message):
    settings = get_settings(msg.from_user.id)
    current  = settings.get("provider", "kling")
    label    = PROVIDER_LABELS.get(current, current)

    text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"Текущий провайдер: <b>{label}</b>\n"
        f"Разрешение: <b>{settings.get('resolution', '720p')}</b>\n"
        f"Длительность: <b>{settings.get('duration', 5)}с</b>\n\n"
        f"Выбери провайдер по умолчанию:"
    )
    await msg.answer(text, reply_markup=settings_kb(current))


@router.callback_query(F.data.startswith("set_provider:"))
async def on_set_provider(cb: CallbackQuery):
    provider = cb.data.split(":")[1]
    set_setting(cb.from_user.id, "provider", provider)
    label = PROVIDER_LABELS.get(provider, provider)
    await cb.message.edit_text(
        f"✅ Провайдер по умолчанию: <b>{label}</b>",
        reply_markup=settings_kb(provider),
    )
    await cb.answer(f"Выбрано: {label}")


@router.callback_query(F.data == "settings:back")
async def on_settings_back(cb: CallbackQuery):
    await cb.message.delete()
    await cb.answer()
