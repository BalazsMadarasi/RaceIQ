"""Preparation helpers for FastF1 lap data."""

import pandas as pd

_TIMING_COLUMNS = {
    "LapTime": "LapTimeSeconds",
    "Sector1Time": "Sector1TimeSeconds",
    "Sector2Time": "Sector2TimeSeconds",
    "Sector3Time": "Sector3TimeSeconds",
}


def prepare_laps(laps: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of lap data with numeric timings and pit-lap flags."""
    prepared = laps.copy()

    for source_column, derived_column in _TIMING_COLUMNS.items():
        if source_column in prepared.columns:
            prepared[derived_column] = prepared[source_column].dt.total_seconds()

    if "PitInTime" in prepared.columns:
        prepared["IsPitInLap"] = prepared["PitInTime"].notna()

    if "PitOutTime" in prepared.columns:
        prepared["IsPitOutLap"] = prepared["PitOutTime"].notna()

    return prepared


def get_recorded_lap_count(laps: pd.DataFrame) -> int | None:
    """Return the highest valid recorded lap number, if one is available."""
    if "LapNumber" not in laps.columns:
        return None

    lap_numbers = pd.to_numeric(laps["LapNumber"], errors="coerce")
    valid_lap_numbers = lap_numbers[
        lap_numbers.ge(1) & lap_numbers.lt(float("inf")) & lap_numbers.mod(1).eq(0)
    ]
    if valid_lap_numbers.empty:
        return None

    return int(valid_lap_numbers.max())
