"""Race-pace filtering and summary calculations."""

import pandas as pd

_EXCLUDED_FLAG_VALUES = {
    "IsPitInLap": True,
    "IsPitOutLap": True,
    "IsAccurate": False,
    "Deleted": True,
}


def filter_representative_laps(laps: pd.DataFrame) -> pd.DataFrame:
    """Return structurally suitable pace laps without statistical outlier filtering."""
    is_representative = laps["LapTimeSeconds"].notna()

    for column, excluded_value in _EXCLUDED_FLAG_VALUES.items():
        if column in laps.columns:
            is_representative &= ~laps[column].eq(excluded_value).fillna(False)

    return laps.loc[is_representative].copy()


def summarize_driver_pace(laps: pd.DataFrame) -> pd.DataFrame:
    """Summarize representative laps per driver using sample standard deviation."""
    representative_laps = filter_representative_laps(laps)
    grouped_lap_times = representative_laps.groupby("Driver", sort=False)["LapTimeSeconds"]

    summary = grouped_lap_times.agg(
        RepresentativeLapCount="count",
        FastestLapSeconds="min",
        MedianLapSeconds="median",
        MeanLapSeconds="mean",
        LapTimeStdSeconds="std",
    ).reset_index()

    if "Team" in representative_laps.columns:
        teams = representative_laps.groupby("Driver", sort=False)["Team"].first()
        summary.insert(1, "Team", summary["Driver"].map(teams))

    return summary.sort_values("MedianLapSeconds").reset_index(drop=True)
