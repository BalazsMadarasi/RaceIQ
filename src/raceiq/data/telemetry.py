"""Data access helpers for selecting laps and retrieving FastF1 telemetry."""

import pandas as pd
from fastf1.core import Session

TELEMETRY_COLUMNS = ("X", "Y", "Speed", "Distance", "Time", "SessionTime")
LAP_OPTION_COLUMNS = ("LapNumber", "LapTime")


def get_available_drivers(session: Session) -> list[str]:
    """Return drivers with a timed, non-deleted lap in session order."""
    laps = session.laps
    if not {"Driver", "LapNumber", "LapTime"}.issubset(laps.columns):
        return []

    suitable = laps["Driver"].notna() & laps["LapNumber"].notna() & laps["LapTime"].notna()
    if "Deleted" in laps.columns:
        suitable &= ~laps["Deleted"].eq(True).fillna(False)

    return laps.loc[suitable, "Driver"].astype(str).drop_duplicates().tolist()


def get_driver_lap_options(session: Session, driver: str) -> pd.DataFrame:
    """Return a driver's timed, non-deleted laps for UI selection."""
    laps = session.laps
    if not {"Driver", *LAP_OPTION_COLUMNS}.issubset(laps.columns):
        return pd.DataFrame(columns=LAP_OPTION_COLUMNS)

    selected = laps.loc[laps["Driver"].eq(driver)].copy()
    selected = selected.loc[selected["LapNumber"].notna() & selected["LapTime"].notna()].copy()
    if "Deleted" in selected.columns:
        selected = selected.loc[~selected["Deleted"].eq(True).fillna(False)].copy()

    selected["LapNumber"] = pd.to_numeric(selected["LapNumber"], errors="coerce")
    selected = selected.dropna(subset=["LapNumber"])
    selected = selected.loc[selected["LapNumber"].mod(1).eq(0)].copy()
    selected["LapNumber"] = selected["LapNumber"].astype(int)

    return (
        selected.loc[:, LAP_OPTION_COLUMNS]
        .drop_duplicates(subset="LapNumber", keep="first")
        .sort_values("LapNumber", kind="stable")
        .reset_index(drop=True)
    )


def get_lap_telemetry(session: Session, driver: str, lap_number: int) -> pd.DataFrame:
    """Return selected merged car/position telemetry channels for one lap."""
    selected_laps = session.laps.pick_drivers(driver).pick_laps(lap_number)
    if selected_laps.empty:
        raise ValueError(f"Lap {lap_number} was not found for driver {driver}.")

    telemetry = selected_laps.iloc[0].get_telemetry()
    available_columns = [column for column in TELEMETRY_COLUMNS if column in telemetry.columns]
    return pd.DataFrame(telemetry.loc[:, available_columns]).copy()
