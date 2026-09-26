"""
Kling AI — Omni Flash model
Docs: https://platform.klingai.com/
"""

import aiohttp
import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Optional

import jwt  # PyJWT

logger = logging.getLogger(__name__)

KLING_MODEL    = "kling-v2-master"   # supports Omni Flash mode
KLING_MODE     = "std"               # std | pro
KLING_BASE_URL = "https://api-singapore.klingai.com"


def _make_jwt(access_key: str, secret_key: str) -> str:
    """Generate Kling JWT token (valid 30 min)."""
    now     = int(time.time())
    payload = {"iss": access_key, "exp": now + 1800, "nbf": now - 5}
    return jwt.encode(payload, secret_key, algorithm="HS256")


class KlingService:
    def __init__(self, access_key: str, secret_key: str, base_url: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url   = base_url or KLING_BASE_URL

    def _headers(self) -> dict:
    return {
        "Authorization": f"Bearer {self.access_key}",
        "Content-Type": "application/json"
    }

    async def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "720p",
        aspect_ratio: str = "16:9",
        negative_prompt: str = "",
    ) -> Optional[str]:
        payload = {
            "model_name":       KLING_MODEL,
            "prompt":           prompt,
            "negative_prompt":  negative_prompt,
            "cfg_scale":        0.5,
            "mode":             KLING_MODE,
            "duration":         str(duration),
            "aspect_ratio":     aspect_ratio,
        }
        return await self._submit("/v1/videos/text2video", payload)

    async def generate_image_to_video(
        self,
        prompt: str,
        image_bytes: bytes,
        duration: int = 5,
        resolution: str = "720p",
    ) -> Optional[str]:
        img_b64 = base64.b64encode(image_bytes).decode()
        payload = {
            "model_name":   KLING_MODEL,
            "prompt":       prompt,
            "mode":         KLING_MODE,
            "duration":     str(duration),
            "image":        img_b64,
        }
        return await self._submit("/v1/videos/image2video", payload)

    async def get_status(self, task_id: str) -> dict:
        url = f"{self.base_url}/v1/videos/text2video/{task_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers()) as r:
                    data = await r.json()
                    task = data.get("data", {})
                    raw_status = task.get("task_status", "unknown")

                    # Map Kling statuses → unified
                    status_map = {
                        "submitted":  "pending",
                        "processing": "processing",
                        "succeed":    "succeed",
                        "failed":     "failed",
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

    async def _submit(self, path: str, payload: dict) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}{path}",
                    headers=self._headers(),
                    json=payload,
                ) as r:
                    data = await r.json()
                    task_id = data.get("data", {}).get("task_id")
                    logger.info(f"Kling task created: {task_id}")
                    return task_id
        except Exception as e:
            logger.error(f"Kling submit error: {e}")
            return None
