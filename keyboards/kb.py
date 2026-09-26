from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ── Main menu ─────────────────────────────────────────────────────────────────

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Генерировать видео")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="📜 История")],
            [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
    )


# ── Provider selection ────────────────────────────────────────────────────────

def provider_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    providers = [
        ("🌱 SeedDance 2.5",  "provider:seedance"),
        ("⚡ Kling Omni Flash", "provider:kling"),
        ("🌊 Luma Flow",        "provider:luma"),
        ("🎥 Runway ML",        "provider:runway"),
    ]
    for label, data in providers:
        builder.button(text=label, callback_data=data)
    builder.adjust(2)
    return builder.as_markup()


# ── Generation mode ───────────────────────────────────────────────────────────

def gen_mode_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Text → Video",  callback_data="mode:t2v")
    builder.button(text="🖼 Image → Video", callback_data="mode:i2v")
    builder.adjust(2)
    return builder.as_markup()


# ── Duration selection ────────────────────────────────────────────────────────

def duration_kb(provider: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Different providers support different durations
    durations = {
        "seedance": ["3s", "5s", "8s"],
        "kling":    ["5s", "10s"],
        "luma":     ["5s", "9s"],
        "runway":   ["5s", "10s"],
    }
    for d in durations.get(provider, ["5s", "10s"]):
        builder.button(text=d, callback_data=f"dur:{d}")
    builder.adjust(3)
    return builder.as_markup()


# ── Resolution selection ──────────────────────────────────────────────────────

def resolution_kb(provider: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    resolutions = {
        "seedance": ["720p", "1080p"],
        "kling":    ["720p", "1080p"],
        "luma":     ["540p", "720p", "1080p"],
        "runway":   ["720p", "1080p"],
    }
    for r in resolutions.get(provider, ["720p", "1080p"]):
        builder.button(text=r, callback_data=f"res:{r}")
    builder.adjust(2)
    return builder.as_markup()


# ── Confirm / Cancel ──────────────────────────────────────────────────────────

def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Генерировать!", callback_data="confirm:yes")
    builder.button(text="❌ Отмена",        callback_data="confirm:no")
    builder.adjust(2)
    return builder.as_markup()


# ── Cancel generation ─────────────────────────────────────────────────────────

def cancel_kb(task_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛑 Отменить", callback_data=f"cancel:{task_id}")
    return builder.as_markup()


# ── Settings ──────────────────────────────────────────────────────────────────

def settings_kb(current_provider: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    all_providers = {
        "seedance": "🌱 SeedDance 2.5",
        "kling":    "⚡ Kling Omni Flash",
        "luma":     "🌊 Luma Flow",
        "runway":   "🎥 Runway ML",
    }
    for key, label in all_providers.items():
        mark = "✅ " if key == current_provider else ""
        builder.button(text=f"{mark}{label}", callback_data=f"set_provider:{key}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="settings:back"))
    return builder.as_markup()
