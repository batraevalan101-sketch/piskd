"""
🎬 AI Video Generation Telegram Bot
Supports: SeedDance 2.5, Kling Omni Flash, Luma Flow, Runway ML Gen-4
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers.start    import router as start_router
from handlers.generate import router as generate_router
from handlers.settings import router as settings_router
from handlers.history  import router as history_router
from services.factory  import ProviderFactory
from utils.middleware  import FactoryMiddleware
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    config  = Config()
    factory = ProviderFactory(config)

    available = factory.available_providers()
    if not available:
        logger.warning("⚠️  No API keys configured! Set at least one provider key.")
    else:
        logger.info(f"✅ Providers ready: {', '.join(available)}")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Inject factory & config into all handlers via middleware
    middleware = FactoryMiddleware(factory, config)
    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)

    # Register routers
    dp.include_router(start_router)
    dp.include_router(generate_router)
    dp.include_router(settings_router)
    dp.include_router(history_router)

    logger.info("🚀 Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
