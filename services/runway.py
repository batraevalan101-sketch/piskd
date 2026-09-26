"""
Runway ML — Gen-3 Alpha Turbo / Gen-4
Docs: https://docs.dev.runwayml.com/
"""

import aiohttp
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

RUNWAY_MODEL   = "gen4_turbo"   # gen3a_turbo | gen4_turbo
RUNWAY_API_URL = "https://api.dev.runwayml.com/v1"


class RunwayService:
    def __init__(self, api_key: str, base_url: str):
        self.api_key  = api_key
        self.base_url = base_url or RUNWAY_API_URL

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
            "X-Runway-Version": "2024-11-06",
        }

    async def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "720p",
        ratio: str = "1280:720",
    ) -> Optional[str]:
        payload = {
            "promptText": prompt,
            "model":      RUNWAY_MODEL,
            "duration":   duration,
            "ratio":      ratio,
        }
        return await self._submit("/image_to_video", payload)

    async def generate_image_to_video(
        self,
        prompt: str,
        image_bytes: bytes,
        duration: int = 5,
        resolution: str = "720p",
    ) -> Optional[str]:
        img_b64  = base64.b64encode(image_bytes).decode()
        img_data = f"data:image/jpeg;base64,{img_b64}"
        payload  = {
            "promptImage": img_data,
            "promptText":  prompt,
            "model":       RUNWAY_MODEL,
            "duration":    duration,
            "ratio":       "1280:720",
        }
        return await self._submit("/image_to_video", payload)

    async def get_status(self, task_id: str) -> dict:
        url = f"{self.base_url}/tasks/{task_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers()) as r:
                    data = await r.json()
                    raw_status = data.get("status", "unknown")

                    # Runway statuses: PENDING | RUNNING | SUCCEEDED | FAILED | CANCELLED
                    status_map = {
                        "PENDING":   "pending",
                        "RUNNING":   "processing",
                        "SUCCEEDED": "succeed",
                        "FAILED":    "failed",
                        "CANCELLED": "failed",
                    }
                    status    = status_map.get(raw_status, raw_status.lower())
                    video_url = None

                    if status == "succeed":
                        outputs   = data.get("output", [])
                        video_url = outputs[0] if outputs else None

                    error = data.get("failure")
                    return {"status": status, "video_url": video_url, "error": error}
        except Exception as e:
            logger.error(f"Runway get_status error: {e}")
            return {"status": "error", "video_url": None}

    async def _submit(self, path: str, payload: dict) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}{path}",
                    headers=self._headers(),
                    json=payload,
                ) as r:
                    data    = await r.json()
                    task_id = data.get("id")
                    logger.info(f"Runway task created: {task_id}")
                    return task_id
        except Exception as e:
            logger.error(f"Runway submit error: {e}")
            return None
