from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class FactoryMiddleware(BaseMiddleware):
    """Injects ProviderFactory and Config into every handler."""

    def __init__(self, factory, config):
        self.factory = factory
        self.config  = config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["factory"] = self.factory
        data["config"]  = self.config
        return await handler(event, data)
