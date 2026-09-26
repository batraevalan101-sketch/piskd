"""
Provider factory — unified interface to all AI video services.
"""

import asyncio
import logging
from typing import Optional

from config import Config
from services.seedance import SeedDanceService
from services.kling    import KlingService
from services.luma     import LumaService
from services.runway   import RunwayService

logger = logging.getLogger(__name__)

PROVIDER_LABELS = {
    "seedance": "🌱 SeedDance 2.5",
    "kling":    "⚡ Kling Omni Flash",
    "luma":     "🌊 Luma Flow",
    "runway":   "🎥 Runway ML",
}


class VideoGenerationResult:
    def __init__(self, task_id: str, provider: str):
        self.task_id  = task_id
        self.provider = provider

    def __repr__(self):
        return f"<VideoGenerationResult {self.provider}:{self.task_id}>"


class ProviderFactory:
    def __init__(self, config: Config):
        self.config = config
        self._clients = {}

    def get_client(self, provider: str):
        if provider in self._clients:
            return self._clients[provider]

        c = self.config
        if provider == "seedance" and c.SEEDANCE_API_KEY:
            client = SeedDanceService(c.SEEDANCE_API_KEY, c.SEEDANCE_API_URL)
        elif provider == "kling" and c.KLING_API_KEY:
    client = KlingService(api_key=c.KLING_API_KEY)
        elif provider == "luma" and c.LUMA_API_KEY:
            client = LumaService(c.LUMA_API_KEY, c.LUMA_API_URL)
        elif provider == "runway" and c.RUNWAY_API_KEY:
            client = RunwayService(c.RUNWAY_API_KEY, c.RUNWAY_API_URL)
        else:
            return None

        self._clients[provider] = client
        return client

    def available_providers(self) -> list[str]:
        """Return list of providers that have API keys configured."""
        all_p = ["seedance", "kling", "luma", "runway"]
        return [p for p in all_p if self.get_client(p) is not None]

    async def submit_text_to_video(
        self,
        provider: str,
        prompt: str,
        duration: int = 5,
        resolution: str = "720p",
    ) -> Optional[VideoGenerationResult]:
        client = self.get_client(provider)
        if not client:
            logger.error(f"Provider '{provider}' not configured")
            return None

        task_id = await client.generate_text_to_video(
            prompt=prompt, duration=duration, resolution=resolution
        )
        return VideoGenerationResult(task_id, provider) if task_id else None

    async def submit_image_to_video(
        self,
        provider: str,
        prompt: str,
        image_bytes: bytes,
        duration: int = 5,
        resolution: str = "720p",
    ) -> Optional[VideoGenerationResult]:
        client = self.get_client(provider)
        if not client:
            return None

        task_id = await client.generate_image_to_video(
            prompt=prompt, image_bytes=image_bytes,
            duration=duration, resolution=resolution,
        )
        return VideoGenerationResult(task_id, provider) if task_id else None

    async def poll_until_done(
        self,
        result: VideoGenerationResult,
        poll_interval: float = 3.0,
        max_wait: int = 300,
    ) -> dict:
        """Poll provider until video is ready or timeout. Returns status dict."""
        client   = self.get_client(result.provider)
        elapsed  = 0

        while elapsed < max_wait:
            status = await client.get_status(result.task_id)
            s      = status.get("status")

            if s in ("succeed", "failed", "error"):
                return status

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        return {"status": "timeout", "video_url": None}
