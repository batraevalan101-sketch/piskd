from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from keyboards.kb import main_menu_kb

router = Router()

WELCOME = """
🎬 <b>AI Video Generator Bot</b>

Генерирую видео с помощью лучших нейросетей:

🌱 <b>SeedDance 2.5</b> — ByteDance, реалистичные сцены
⚡ <b>Kling Omni Flash</b> — быстро, высокое качество
🌊 <b>Luma Flow</b> — кинематографичный стиль
🎥 <b>Runway ML Gen-4</b> — профессиональный уровень

<b>Как пользоваться:</b>
1. Нажми <b>🎬 Генерировать видео</b>
2. Выбери нейросеть и режим (текст или фото → видео)
3. Введи описание или отправь изображение
4. Подожди — видео придёт прямо в чат!

⚙️ В настройках можно выбрать провайдера по умолчанию.
"""


@router.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer(WELCOME, reply_markup=main_menu_kb())


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(msg: Message):
    await msg.answer(WELCOME, reply_markup=main_menu_kb())
