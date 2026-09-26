import asyncio
import logging
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from keyboards.kb import (
    provider_kb, gen_mode_kb, duration_kb,
    resolution_kb, confirm_kb, cancel_kb,
)
from services.factory import ProviderFactory, PROVIDER_LABELS
from utils.storage import get_settings, set_setting, add_history
from config import Config

logger = logging.getLogger(__name__)
router = Router()

# ── States ─────────────────────────────────────────────────────────────────────

class GenState(StatesGroup):
    choose_provider  = State()
    choose_mode      = State()
    choose_duration  = State()
    choose_resolution = State()
    awaiting_prompt  = State()
    awaiting_image   = State()
    confirming       = State()
    generating       = State()


# ── Factory instance (injected via middleware or dispatcher data) ───────────────
# We use Bot's data storage to pass factory; in bot.py pass it in dispatcher data.

def _factory(state_data: dict) -> ProviderFactory:
    return state_data["factory"]


# ── Entry point ────────────────────────────────────────────────────────────────

@router.message(F.text == "🎬 Генерировать видео")
@router.message(Command("generate"))
async def start_generate(msg: Message, state: FSMContext, factory: ProviderFactory):
    settings = get_settings(msg.from_user.id)
    await state.update_data(factory=None)  # factory passed separately
    await state.update_data(
        user_id=msg.from_user.id,
        provider=settings.get("provider", "kling"),
        duration=settings.get("duration", 5),
        resolution=settings.get("resolution", "720p"),
        mode=None,
        prompt=None,
        image_bytes=None,
    )
    await msg.answer("🎬 <b>Выбери нейросеть:</b>", reply_markup=provider_kb())
    await state.set_state(GenState.choose_provider)


# ── Provider chosen ────────────────────────────────────────────────────────────

@router.callback_query(GenState.choose_provider, F.data.startswith("provider:"))
async def on_provider(cb: CallbackQuery, state: FSMContext):
    provider = cb.data.split(":")[1]
    await state.update_data(provider=provider)
    label = PROVIDER_LABELS.get(provider, provider)
    await cb.message.edit_text(
        f"✅ Выбрано: <b>{label}</b>\n\n🎞 <b>Режим генерации:</b>",
        reply_markup=gen_mode_kb(),
    )
    await state.set_state(GenState.choose_mode)
    await cb.answer()


# ── Mode chosen ────────────────────────────────────────────────────────────────

@router.callback_query(GenState.choose_mode, F.data.startswith("mode:"))
async def on_mode(cb: CallbackQuery, state: FSMContext):
    mode = cb.data.split(":")[1]
    data = await state.get_data()
    await state.update_data(mode=mode)
    await cb.message.edit_text(
        "⏱ <b>Длительность видео:</b>",
        reply_markup=duration_kb(data["provider"]),
    )
    await state.set_state(GenState.choose_duration)
    await cb.answer()


# ── Duration chosen ────────────────────────────────────────────────────────────

@router.callback_query(GenState.choose_duration, F.data.startswith("dur:"))
async def on_duration(cb: CallbackQuery, state: FSMContext):
    dur_str  = cb.data.split(":")[1]          # e.g. "5s"
    duration = int(dur_str.replace("s", ""))
    data     = await state.get_data()
    await state.update_data(duration=duration)
    await cb.message.edit_text(
        "🖥 <b>Разрешение видео:</b>",
        reply_markup=resolution_kb(data["provider"]),
    )
    await state.set_state(GenState.choose_resolution)
    await cb.answer()


# ── Resolution chosen ──────────────────────────────────────────────────────────

@router.callback_query(GenState.choose_resolution, F.data.startswith("res:"))
async def on_resolution(cb: CallbackQuery, state: FSMContext):
    resolution = cb.data.split(":")[1]
    await state.update_data(resolution=resolution)
    data = await state.get_data()

    if data["mode"] == "t2v":
        await cb.message.edit_text("✏️ <b>Введи описание для видео:</b>\n\nПример: <i>A futuristic city at sunset, cinematic, 4K</i>")
        await state.set_state(GenState.awaiting_prompt)
    else:
        await cb.message.edit_text("🖼 <b>Отправь изображение</b>, которое хочешь оживить:")
        await state.set_state(GenState.awaiting_image)
    await cb.answer()


# ── Receive prompt (T2V) ───────────────────────────────────────────────────────

@router.message(GenState.awaiting_prompt, F.text)
async def on_prompt(msg: Message, state: FSMContext):
    prompt = msg.text.strip()
    if len(prompt) < 3:
        await msg.answer("⚠️ Описание слишком короткое. Попробуй ещё раз:")
        return

    await state.update_data(prompt=prompt)
    data = await state.get_data()
    await _show_confirm(msg, data)
    await state.set_state(GenState.confirming)


# ── Receive image (I2V) ────────────────────────────────────────────────────────

@router.message(GenState.awaiting_image, F.photo)
async def on_image(msg: Message, state: FSMContext, bot: Bot):
    photo   = msg.photo[-1]   # largest resolution
    file    = await bot.get_file(photo.file_id)
    buf     = await bot.download_file(file.file_path)
    img_bytes = buf.read()
    await state.update_data(image_bytes=img_bytes)

    await msg.answer(
        "✏️ <b>Введи описание для анимации</b> (или нажми /skip для авто):"
    )
    await state.set_state(GenState.awaiting_prompt)


@router.message(GenState.awaiting_image)
async def on_bad_image(msg: Message):
    await msg.answer("📸 Пожалуйста, отправь именно <b>изображение</b>.")


# ── Skip prompt for I2V ────────────────────────────────────────────────────────

@router.message(GenState.awaiting_prompt, Command("skip"))
async def on_skip_prompt(msg: Message, state: FSMContext):
    await state.update_data(prompt="Animate this image smoothly and naturally")
    data = await state.get_data()
    await _show_confirm(msg, data)
    await state.set_state(GenState.confirming)


# ── Confirm ────────────────────────────────────────────────────────────────────

async def _show_confirm(msg: Message, data: dict):
    provider  = data.get("provider", "kling")
    label     = PROVIDER_LABELS.get(provider, provider)
    mode_text = "Текст → Видео" if data.get("mode") == "t2v" else "Фото → Видео"
    prompt    = data.get("prompt", "—")[:200]

    text = (
        f"📋 <b>Параметры генерации:</b>\n\n"
        f"🤖 Нейросеть: <b>{label}</b>\n"
        f"🎞 Режим: <b>{mode_text}</b>\n"
        f"⏱ Длительность: <b>{data.get('duration', 5)}с</b>\n"
        f"🖥 Разрешение: <b>{data.get('resolution', '720p')}</b>\n"
        f"✏️ Промпт: <i>{prompt}</i>"
    )
    await msg.answer(text, reply_markup=confirm_kb())


@router.callback_query(GenState.confirming, F.data == "confirm:no")
async def on_cancel_confirm(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ Генерация отменена.")
    await cb.answer()


@router.callback_query(GenState.confirming, F.data == "confirm:yes")
async def on_confirm(cb: CallbackQuery, state: FSMContext, factory: ProviderFactory):
    data = await state.get_data()
    await state.set_state(GenState.generating)

    provider   = data["provider"]
    prompt     = data["prompt"]
    mode       = data["mode"]
    duration   = data["duration"]
    resolution = data["resolution"]
    label      = PROVIDER_LABELS.get(provider, provider)

    status_msg = await cb.message.edit_text(
        f"⏳ <b>Генерирую видео...</b>\n\n"
        f"🤖 {label}\n"
        f"Это может занять от 30 секунд до нескольких минут.",
    )

    # Submit generation task
    if mode == "t2v":
        result = await factory.submit_text_to_video(
            provider, prompt, duration, resolution
        )
    else:
        result = await factory.submit_image_to_video(
            provider, prompt, data.get("image_bytes", b""), duration, resolution
        )

    if not result:
        await status_msg.edit_text("❌ Ошибка при создании задачи. Проверь API ключи.")
        await state.clear()
        await cb.answer()
        return

    await status_msg.edit_text(
        f"⏳ <b>Задача принята!</b>\n🆔 <code>{result.task_id}</code>\n\nОжидаем результат...",
        reply_markup=cancel_kb(result.task_id),
    )

    # Poll in background
    asyncio.create_task(
        _poll_and_deliver(
            bot=cb.bot,
            chat_id=cb.from_user.id,
            status_msg_id=status_msg.message_id,
            result=result,
            factory=factory,
            state=state,
            user_data=data,
        )
    )
    await cb.answer()


async def _poll_and_deliver(
    bot: Bot,
    chat_id: int,
    status_msg_id: int,
    result,
    factory: ProviderFactory,
    state: FSMContext,
    user_data: dict,
):
    """Background task: polls until video is ready and sends it to user."""
    try:
        status = await factory.poll_until_done(result)
        s      = status.get("status")

        if s == "succeed" and status.get("video_url"):
            # Download video
            import aiohttp
            video_url = status["video_url"]
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as r:
                    video_bytes = await r.read()

            provider_label = PROVIDER_LABELS.get(result.provider, result.provider)
            caption = (
                f"🎬 <b>Видео готово!</b>\n\n"
                f"🤖 {provider_label}\n"
                f"✏️ <i>{user_data.get('prompt', '')[:150]}</i>"
            )

            await bot.send_video(
                chat_id,
                video=BufferedInputFile(video_bytes, filename="video.mp4"),
                caption=caption,
                supports_streaming=True,
            )
            await bot.delete_message(chat_id, status_msg_id)

            # Save to history
            add_history(chat_id, {
                "date":      datetime.now().isoformat(),
                "provider":  result.provider,
                "prompt":    user_data.get("prompt", ""),
                "duration":  user_data.get("duration"),
                "status":    "succeed",
            })

        elif s == "timeout":
            await bot.edit_message_text(
                "⏰ <b>Превышено время ожидания.</b>\nПопробуй снова чуть позже.",
                chat_id=chat_id, message_id=status_msg_id,
            )
        else:
            err = status.get("error") or "Неизвестная ошибка"
            await bot.edit_message_text(
                f"❌ <b>Ошибка генерации:</b> {err}",
                chat_id=chat_id, message_id=status_msg_id,
            )
    except Exception as e:
        logger.error(f"Poll/deliver error: {e}", exc_info=True)
        try:
            await bot.edit_message_text(
                "❌ Произошла ошибка. Попробуй снова.",
                chat_id=chat_id, message_id=status_msg_id,
            )
        except Exception:
            pass
    finally:
        await state.clear()


# ── Cancel running task ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cancel:"))
async def on_cancel_task(cb: CallbackQuery, state: FSMContext):
    # We can't truly cancel API tasks mid-flight in most providers,
    # but we clear local state and inform the user.
    await state.clear()
    await cb.message.edit_text("🛑 <b>Задача отменена.</b>\nВидео может продолжить генерироваться на стороне провайдера.")
    await cb.answer("Отменено")
