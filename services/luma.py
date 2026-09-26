"""
Luma Dream Machine — Flow model
Docs: https://lumalabs.ai/dream-machine/api/docs
"""

import aiohttp
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

LUMA_MODEL   = "dream-machine"   # dream-machine (Flow)
LUMA_API_URL = "https://api.lumalabs.ai"


class LumaService:
    def __init__(self, api_key: str, base_url: str):
        self.api_key  = api_key
        self.base_url = base_url or LUMA_API_URL

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }

    async def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "720p",
        aspect_ratio: str = "16:9",
        loop: bool = False,
    ) -> Optional[str]:
        payload = {
            "prompt":         prompt,
            "aspect_ratio":   aspect_ratio,
            "loop":           loop,
            "model":          LUMA_MODEL,
        }
        return await self._submit("/dream-machine/v1/generations", payload)

    async def generate_image_to_video(
        self,
        prompt: str,
        image_bytes: bytes,
        duration: int = 5,
        resolution: str = "720p",
    ) -> Optional[str]:
        # Upload image first, then reference it
        img_b64  = base64.b64encode(image_bytes).decode()
        img_data = f"data:image/jpeg;base64,{img_b64}"

        payload = {
            "prompt":    prompt,
            "keyframes": {
                "frame0": {"type": "image", "url": img_data},
            },
            "model":     LUMA_MODEL,
        }
        return await self._submit("/dream-machine/v1/generations", payload)

    async def get_status(self, task_id: str) -> dict:
        url = f"{self.base_url}/dream-machine/v1/generations/{task_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers()) as r:
                    data = await r.json()
                    raw_state = data.get("state", "unknown")

                    # Luma states: queued | dreaming | completed | failed
                    state_map = {
                        "queued":    "pending",
                        "dreaming":  "processing",
                        "completed": "succeed",
                        "failed":    "failed",
                    }
                    status    = state_map.get(raw_state, raw_state)
                    video_url = None

                    if status == "succeed":
                        video_url = (data.get("assets", {}).get("video"))

                    failure = data.get("failure_reason")
                    return {"status": status, "video_url": video_url, "error": failure}
        except Exception as e:
            logger.error(f"Luma get_status error: {e}")
            return {"status": "error", "video_url": None}

    async def _submit(self, path: str, payload: dict) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}{path}",
                    headers=self._headers(),
                    json=payload,
                ) as r:
                    data = await r.json()
                    gen_id = data.get("id")
                    logger.info(f"Luma generation created: {gen_id}")
                    return gen_id
        except Exception as e:
            logger.error(f"Luma submit error: {e}")
            return None
