"""Configuration settings for Windows Keyboard Analytics."""

from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True)
class Settings:
    """Application runtime configuration with defaults."""

    host: str
    port: int
    db_path: Path
    batch_interval_sec: float
    batch_max_size: int


def get_app_dir() -> Path:
    """Return the persistent base directory (next to the executable when frozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_resource_dir() -> Path:
    """Return the bundled static resource directory (supports PyInstaller _MEIPASS)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parent.parent


def load_settings() -> Settings:
    """Load default application settings."""
    base_dir = get_app_dir()
    return Settings(
        host="127.0.0.1",
        port=8765,
        db_path=base_dir / "data" / "keyboard_analytics.db",
        batch_interval_sec=0.25,
        batch_max_size=50,
    )
