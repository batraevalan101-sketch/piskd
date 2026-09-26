"""
SeedDance 2.5 — ByteDance VolcEngine API
Docs: https://www.volcengine.com/docs/6791/1359512
"""

import asyncio
import aiohttp
import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

SEEDANCE_MODEL = "seedance-1-lite"   # seedance-1-lite | seedance-1-pro


def _sign_request(access_key: str, secret_key: str, method: str,
                  host: str, path: str, payload: dict) -> dict:
    """Generate VolcEngine V4 signature headers."""
    now = datetime.now(timezone.utc)
    date_str  = now.strftime("%Y%m%d")
    time_str  = now.strftime("%Y%m%dT%H%M%SZ")
    service   = "visual"
    region    = "cn-north-1"

    body = json.dumps(payload, ensure_ascii=False).encode()
    body_hash = hashlib.sha256(body).hexdigest()

    canonical_headers = f"content-type:application/json\nhost:{host}\nx-date:{time_str}\n"
    signed_headers    = "content-type;host;x-date"
    canonical_request = "\n".join([method, path, "", canonical_headers,
                                   signed_headers, body_hash])

    credential_scope = f"{date_str}/{region}/{service}/request"
    string_to_sign   = "\n".join(["HMAC-SHA256", time_str, credential_scope,
                                   hashlib.sha256(canonical_request.encode()).hexdigest()])

    def _hmac(key, msg):
        return hmac.new(key if isinstance(key, bytes) else key.encode(),
                        msg.encode(), hashlib.sha256).digest()

    signing_key = _hmac(_hmac(_hmac(_hmac(secret_key, date_str), region), service), "request")
    signature   = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

    auth = (f"HMAC-SHA256 Credential={access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}")

    return {
        "Content-Type": "application/json",
        "Host": host,
        "X-Date": time_str,
        "Authorization": auth,
    }


class SeedDanceService:
    def __init__(self, api_key: str, base_url: str):
        # For SeedDance we use api_key as access_key;
        # set SEEDANCE_SECRET_KEY env separately for signing.
        import os
        self.access_key = api_key
        self.secret_key = os.getenv("SEEDANCE_SECRET_KEY", "")
        self.host = base_url.replace("https://", "").replace("http://", "")
        self.base_url = base_url

    async def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "720p",
        aspect_ratio: str = "16:9",
    ) -> Optional[str]:
        """Submit text-to-video task, return task_id."""
        width, height = self._resolution_to_wh(resolution)
        payload = {
            "model_id": SEEDANCE_MODEL,
            "content": [{"type": "text", "text": prompt}],
            "parameters": {
                "duration": duration,
                "resolution": f"{width}x{height}",
                "aspect_ratio": aspect_ratio,
            },
        }
        return await self._submit(payload)

    async def generate_image_to_video(
        self,
        prompt: str,
        image_bytes: bytes,
        duration: int = 5,
        resolution: str = "720p",
    ) -> Optional[str]:
        """Submit image-to-video task, return task_id."""
        img_b64 = base64.b64encode(image_bytes).decode()
        width, height = self._resolution_to_wh(resolution)
        payload = {
            "model_id": SEEDANCE_MODEL,
            "content": [
                {"type": "image", "image_base64": img_b64},
                {"type": "text", "text": prompt},
            ],
            "parameters": {
                "duration": duration,
                "resolution": f"{width}x{height}",
            },
        }
        return await self._submit(payload)

    async def get_status(self, task_id: str) -> dict:
        """Poll task status. Returns dict with 'status' and optionally 'video_url'."""
        path    = f"/api/v1/contents/generations/{task_id}"
        headers = _sign_request(self.access_key, self.secret_key,
                                 "GET", self.host, path, {})
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{path}", headers=headers) as r:
                    data = await r.json()
                    status = data.get("data", {}).get("status", "unknown")
                    video_url = None
                    if status == "succeed":
                        video_url = (data.get("data", {})
                                     .get("contents", [{}])[0]
                                     .get("video_url"))
                    return {"status": status, "video_url": video_url, "raw": data}
        except Exception as e:
            logger.error(f"SeedDance get_status error: {e}")
            return {"status": "error", "video_url": None}

    async def _submit(self, payload: dict) -> Optional[str]:
        path    = "/api/v1/contents/generations/tasks"
        headers = _sign_request(self.access_key, self.secret_key,
                                 "POST", self.host, path, payload)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}{path}",
                    headers=headers,
                    json=payload,
                ) as r:
                    data = await r.json()
                    task_id = data.get("data", {}).get("task_id")
                    logger.info(f"SeedDance task created: {task_id}")
                    return task_id
        except Exception as e:
            logger.error(f"SeedDance submit error: {e}")
            return None

    @staticmethod
    def _resolution_to_wh(resolution: str) -> tuple[int, int]:
        mapping = {"540p": (960, 540), "720p": (1280, 720), "1080p": (1920, 1080)}
        return mapping.get(resolution, (1280, 720))
