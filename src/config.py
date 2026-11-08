"""Configuration settings for Windows Keyboard Analytics."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application runtime configuration with defaults."""

    host: str
    port: int
    db_path: Path
    batch_interval_sec: float
    batch_max_size: int


def load_settings() -> Settings:
    """Load default application settings."""
    base_dir = Path(__file__).resolve().parent.parent
    return Settings(
        host="127.0.0.1",
        port=8765,
        db_path=base_dir / "data" / "keyboard_analytics.db",
        batch_interval_sec=0.25,
        batch_max_size=50,
    )
