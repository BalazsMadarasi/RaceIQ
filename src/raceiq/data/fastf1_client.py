"""Small data-access boundary for loading FastF1 sessions."""

from pathlib import Path

import fastf1
import pandas as pd
from fastf1.core import Session

DEFAULT_CACHE_DIR = Path("data/cache")
SESSION_COLUMNS = tuple(f"Session{number}" for number in range(1, 6))


def enable_fastf1_cache(cache_dir: Path | str = DEFAULT_CACHE_DIR) -> None:
    """Create and enable the local FastF1 cache directory."""
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_path))


def get_event_schedule(year: int) -> fastf1.events.EventSchedule:
    """Return the non-testing FastF1 event schedule for a season."""
    enable_fastf1_cache()
    return fastf1.get_event_schedule(year, include_testing=False)


def get_event_names(year: int) -> list[str]:
    """Return available Grand Prix names for a season in calendar order."""
    return list(get_event_session_options(year))


def get_event_session_options(year: int) -> dict[str, list[str]]:
    """Return each event's available sessions in chronological order."""
    schedule = get_event_schedule(year)
    event_sessions: dict[str, list[str]] = {}

    for _, event in schedule.iterrows():
        event_name = event.get("EventName")
        if pd.isna(event_name):
            continue

        sessions = [
            str(session_name)
            for column in SESSION_COLUMNS
            if pd.notna(session_name := event.get(column)) and str(session_name).strip()
        ]
        event_sessions[str(event_name)] = sessions

    return event_sessions


def load_session(
    year: int,
    event: str,
    session_type: str,
    *,
    telemetry: bool = True,
    weather: bool = True,
) -> Session:
    """Load and return a FastF1 session using the local cache."""
    enable_fastf1_cache()
    session = fastf1.get_session(year, event, session_type)
    session.load(telemetry=telemetry, weather=weather)
    return session
