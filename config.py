import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    # ── Telegram ──────────────────────────────────────────────
    BOT_TOKEN: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])

    # ── SeedDance (ByteDance) ─────────────────────────────────
    # https://www.volcengine.com/  (VolcEngine API)
    SEEDANCE_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("SEEDANCE_API_KEY")
    )
    SEEDANCE_API_URL: str = "https://visual.volcengineapi.com"

    # ── Kling AI (Omni Flash) ─────────────────────────────────
    # https://platform.klingai.com/
    KLING_ACCESS_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("KLING_ACCESS_KEY")
    )
    KLING_SECRET_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("KLING_SECRET_KEY")
    )
    KLING_API_URL: str = "https://api.klingai.com"

    # ── Luma Dream Machine (Flow) ─────────────────────────────
    # https://lumalabs.ai/dream-machine/api
    LUMA_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("LUMA_API_KEY")
    )
    LUMA_API_URL: str = "https://api.lumalabs.ai"

    # ── Runway ML ─────────────────────────────────────────────
    # https://runwayml.com/
    RUNWAY_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("RUNWAY_API_KEY")
    )
    RUNWAY_API_URL: str = "https://api.dev.runwayml.com/v1"

    # ── Bot settings ──────────────────────────────────────────
    MAX_QUEUE_SIZE: int = 10          # max concurrent tasks
    POLL_INTERVAL: float = 3.0        # seconds between status checks
    MAX_WAIT_SECONDS: int = 300       # max wait for video generation
    DEFAULT_PROVIDER: str = "kling"   # seedance | kling | luma | runway

    # ── Optional: Admin ───────────────────────────────────────
    ADMIN_IDS: list = field(
        default_factory=lambda: [
            int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x
        ]
    )
