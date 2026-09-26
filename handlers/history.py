from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from services.factory import PROVIDER_LABELS
from utils.storage import get_history

router = Router()


@router.message(F.text == "📜 История")
@router.message(Command("history"))
async def cmd_history(msg: Message):
    history = get_history(msg.from_user.id)

    if not history:
        await msg.answer("📜 История генераций пуста.\n\nНажми <b>🎬 Генерировать видео</b>, чтобы начать!")
        return

    lines = ["📜 <b>История генераций</b> (последние 20):\n"]
    for i, entry in enumerate(history[:10], 1):
        provider = PROVIDER_LABELS.get(entry.get("provider", "?"), entry.get("provider", "?"))
        prompt   = entry.get("prompt", "")[:60]
        date     = entry.get("date", "")[:10]
        status   = "✅" if entry.get("status") == "succeed" else "❌"
        dur      = entry.get("duration", "?")
        lines.append(f"{i}. {status} {provider}\n   📅 {date} | ⏱ {dur}с\n   <i>{prompt}…</i>\n")

    await msg.answer("\n".join(lines))
