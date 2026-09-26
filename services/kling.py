import aiohttp
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

KLING_BASE_URL = "https://api-singapore.klingai.com"


class KlingService:
    def __init__(self, api_key: str, base_url: str = KLING_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _submit(self, path: str, payload: dict) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}{path}",
                    headers=self._headers(),
                    json=payload,
                ) as r:
                    data = await r.json()
                    logger.info(f"Kling full response: {data}")
                    task_id = data.get("data", {}).get("task_id")
                    logger.info(f"Kling task created: {task_id}")
                    return task_id
        except Exception as e:
            logger.error(f"Kling submit error: {e}")
            return None

    async def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "720p",
        aspect_ratio: str = "16:9",
        negative_prompt: str = ""
    ) -> Optional[str]:
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }
        return await self._submit("/text-to-video/kling-3.0-turbo", payload)

    async def generate_image_to_video(
        self,
        prompt: str,
        image_bytes: bytes,
        duration: int = 5,
        resolution: str = "720p",
    ) -> Optional[str]:
        img_b64 = base64.b64encode(image_bytes).decode()
        payload = {
            "contents": [
                {"type": "image", "data": img_b64},
                {"type": "prompt", "text": prompt},
            ],
            "duration": duration,
        }
        return await self._submit("/image-to-video/kling-3.0-turbo", payload)

    async def get_status(self, task_id: str, is_image2video: bool = False) -> dict:
        path = "/image-to-video/kling-3.0-turbo" if is_image2video else "/text-to-video/kling-3.0-turbo"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}{path}/{task_id}",
                    headers=self._headers(),
                ) as r:
                    data = await r.json()
                    logger.info(f"Kling status response: {data}")
                    task = data.get("data", {})
                    raw_status = task.get("task_status", "unknown")
                    status_map = {
                        "submitted": "pending",
                        "processing": "processing",
                        "succeed": "succeed",
                        "failed": "failed",
                    }
                    status = status_map.get(raw_status, raw_status)
                    video_url = None
                    if status == "succeed":
                        videos = task.get("task_result", {}).get("videos", [])
                        if videos:
                            video_url = videos[0].get("url")
                    return {"status": status, "video_url": video_url}
        except Exception as e:
            logger.error(f"Kling get_status error: {e}")
            return {"status": "error", "video_url": None}
