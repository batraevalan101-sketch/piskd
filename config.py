import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    # ── Telegram ──────────────────────────────────────────────
    BOT_TOKEN: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])

    # ── SeedDance (ByteDance) ─────────────────────────────────
    SEEDANCE_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("SEEDANCE_API_KEY")
    )
    SEEDANCE_API_URL: str = "https://visual.volcengineapi.com"

    # ── Kling AI ──────────────────────────────────────────────
    KLING_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("KLING_API_KEY")
    )
    KLING_API_URL: str = "https://api-singapore.klingai.com"

    # ── Luma Dream Machine ────────────────────────────────────
    LUMA_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("LUMA_API_KEY")
    )
    LUMA_API_URL: str = "https://api.lumalabs.ai"

    # ── Runway ML ─────────────────────────────────────────────
    RUNWAY_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("RUNWAY_API_KEY")
    )
    RUNWAY_API_URL: str = "https://api.dev.runwayml.com/v1"

    # ── Bot settings ──────────────────────────────────────────
    MAX_QUEUE_SIZE: int = 10
    POLL_INTERVAL: float = 3.0
    MAX_WAIT_SECONDS: int = 300
    DEFAULT_PROVIDER: str = "kling"

    # ── Optional: Admin ───────────────────────────────────────
    ADMIN_IDS: list = field(
        default_factory=lambda: [
            int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x
        ]
    )
