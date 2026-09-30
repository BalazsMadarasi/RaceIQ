"""Data access helpers for selecting laps and retrieving FastF1 telemetry."""

import logging

import pandas as pd
from fastf1.core import Session
from fastf1.exceptions import DataNotLoadedError

TELEMETRY_COLUMNS = ("X", "Y", "Speed", "Distance", "Time", "SessionTime")
LAP_OPTION_COLUMNS = ("LapNumber", "LapTime")
REQUIRED_LAP_TELEMETRY_COLUMNS = ("X", "Y", "Speed", "Distance")

LOGGER = logging.getLogger(__name__)


class TelemetryUnavailableError(RuntimeError):
    """Base error for telemetry that FastF1 cannot provide."""


class SessionTelemetryUnavailableError(TelemetryUnavailableError):
    """Raised when a session's car or position stream was not loaded."""


class DriverTelemetryUnavailableError(TelemetryUnavailableError):
    """Raised when telemetry streams are missing for one driver."""


class LapTelemetryUnavailableError(TelemetryUnavailableError):
    """Raised when one lap has no complete telemetry trajectory."""


def validate_session_telemetry(session: Session) -> None:
    """Ensure both FastF1 source streams are loaded before caching a session."""
    try:
        car_data = session.car_data
        position_data = session.pos_data
    except DataNotLoadedError as error:
        LOGGER.exception("FastF1 did not load both telemetry streams for the session.")
        raise SessionTelemetryUnavailableError(
            "FastF1 did not load the session's car and position telemetry."
        ) from error

    if not car_data or not position_data:
        LOGGER.error(
            "FastF1 returned empty telemetry mappings (car=%s, position=%s).",
            bool(car_data),
            bool(position_data),
        )
        raise SessionTelemetryUnavailableError(
            "FastF1 returned empty car or position telemetry for the session."
        )


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
        raise LapTelemetryUnavailableError(f"Lap {lap_number} was not found for driver {driver}.")

    selected_lap = selected_laps.iloc[0]
    driver_number = str(selected_lap.get("DriverNumber", "")).strip()

    try:
        validate_session_telemetry(session)
        car_data = session.car_data
        position_data = session.pos_data
    except SessionTelemetryUnavailableError:
        raise

    if (
        not driver_number
        or driver_number not in car_data
        or driver_number not in position_data
        or car_data[driver_number].empty
        or position_data[driver_number].empty
    ):
        LOGGER.error(
            "Telemetry streams are incomplete for driver %s (number=%s).",
            driver,
            driver_number or "unknown",
        )
        raise DriverTelemetryUnavailableError(
            f"Car or position telemetry is unavailable for driver {driver}."
        )

    try:
        telemetry = selected_lap.get_telemetry()
    except DataNotLoadedError as error:
        LOGGER.exception("FastF1 lost access to session telemetry while merging a lap.")
        raise SessionTelemetryUnavailableError(
            "FastF1 could not access the session telemetry streams."
        ) from error
    except KeyError as error:
        LOGGER.exception(
            "FastF1 could not find driver %s while merging lap %s telemetry.",
            driver,
            lap_number,
        )
        raise DriverTelemetryUnavailableError(
            f"Telemetry is unavailable for driver {driver}."
        ) from error

    if telemetry.empty:
        raise LapTelemetryUnavailableError(
            f"Lap {lap_number} for {driver} contains no telemetry samples."
        )

    missing_columns = [
        column for column in REQUIRED_LAP_TELEMETRY_COLUMNS if column not in telemetry.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        LOGGER.error(
            "Lap %s for %s is missing required telemetry columns: %s.",
            lap_number,
            driver,
            missing,
        )
        raise LapTelemetryUnavailableError(
            f"Lap {lap_number} for {driver} is missing required telemetry channels."
        )

    available_columns = [column for column in TELEMETRY_COLUMNS if column in telemetry.columns]
    return pd.DataFrame(telemetry.loc[:, available_columns]).copy()
