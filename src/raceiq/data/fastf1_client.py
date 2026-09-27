"""Small data-access boundary for loading FastF1 sessions."""

from pathlib import Path

import fastf1
from fastf1.core import Session

DEFAULT_CACHE_DIR = Path("data/cache")


def enable_fastf1_cache(cache_dir: Path | str = DEFAULT_CACHE_DIR) -> None:
    """Create and enable the local FastF1 cache directory."""
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_path))


def load_session(year: int, event: str, session_type: str) -> Session:
    """Load and return a FastF1 session using the local cache."""
    enable_fastf1_cache()
    session = fastf1.get_session(year, event, session_type)
    session.load()
    return session
