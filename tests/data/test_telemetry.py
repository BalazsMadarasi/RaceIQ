import pandas as pd
import pytest
from fastf1.exceptions import DataNotLoadedError

from raceiq.data.telemetry import (
    DriverTelemetryUnavailableError,
    LapTelemetryUnavailableError,
    SessionTelemetryUnavailableError,
    get_available_drivers,
    get_driver_lap_options,
    get_lap_telemetry,
    validate_session_telemetry,
)


class FakeSession:
    def __init__(self, laps: pd.DataFrame) -> None:
        self.laps = laps


class FailedTelemetrySession:
    @property
    def car_data(self) -> dict:
        raise DataNotLoadedError("car data")

    @property
    def pos_data(self) -> dict:
        raise AssertionError("position data should not be accessed")


class FakeLap:
    def __init__(self, telemetry: pd.DataFrame, driver_number: str = "1") -> None:
        self.telemetry = telemetry
        self.driver_number = driver_number

    def get(self, key: str, default: str = "") -> str:
        return self.driver_number if key == "DriverNumber" else default

    def get_telemetry(self) -> pd.DataFrame:
        return self.telemetry


class FakePickedLaps:
    empty = False

    def __init__(self, lap: FakeLap) -> None:
        self.iloc = [lap]


class FakeSelectableLaps:
    def __init__(self, lap: FakeLap) -> None:
        self.lap = lap

    def pick_drivers(self, driver: str) -> "FakeSelectableLaps":
        return self

    def pick_laps(self, lap_number: int) -> FakePickedLaps:
        return FakePickedLaps(self.lap)


class FakeTelemetrySession:
    def __init__(
        self,
        lap: FakeLap,
        car_data: dict[str, pd.DataFrame],
        pos_data: dict[str, pd.DataFrame],
    ) -> None:
        self.laps = FakeSelectableLaps(lap)
        self.car_data = car_data
        self.pos_data = pos_data


def test_driver_and_lap_options_require_timed_non_deleted_laps() -> None:
    session = FakeSession(
        pd.DataFrame(
            {
                "Driver": ["AAA", "AAA", "AAA", "BBB", "CCC"],
                "LapNumber": [1.0, 2.0, 3.0, 1.0, 1.0],
                "LapTime": [
                    pd.Timedelta(seconds=90),
                    pd.Timedelta(seconds=89),
                    pd.NaT,
                    pd.Timedelta(seconds=91),
                    pd.Timedelta(seconds=92),
                ],
                "Deleted": [False, True, False, False, True],
            }
        )
    )

    assert get_available_drivers(session) == ["AAA", "BBB"]
    options = get_driver_lap_options(session, "AAA")
    assert options["LapNumber"].tolist() == [1]
    assert options.loc[0, "LapTime"] == pd.Timedelta(seconds=90)


def test_session_validation_rejects_a_suppressed_fastf1_load_failure() -> None:
    with pytest.raises(SessionTelemetryUnavailableError, match="did not load"):
        validate_session_telemetry(FailedTelemetrySession())


def test_session_validation_rejects_an_empty_source_stream() -> None:
    session = type(
        "EmptyTelemetrySession",
        (),
        {"car_data": {"1": pd.DataFrame({"Speed": [200]})}, "pos_data": {}},
    )()

    with pytest.raises(SessionTelemetryUnavailableError, match="empty"):
        validate_session_telemetry(session)


def test_lap_telemetry_distinguishes_missing_driver_streams() -> None:
    samples = pd.DataFrame({"Speed": [200]})
    session = FakeTelemetrySession(
        FakeLap(samples, driver_number="4"),
        car_data={"1": samples},
        pos_data={"1": samples},
    )

    with pytest.raises(DriverTelemetryUnavailableError, match="AAA"):
        get_lap_telemetry(session, "AAA", 7)


def test_lap_telemetry_rejects_missing_required_channels() -> None:
    samples = pd.DataFrame({"Speed": [200]})
    session = FakeTelemetrySession(
        FakeLap(pd.DataFrame({"X": [1], "Y": [2], "Speed": [200]})),
        car_data={"1": samples},
        pos_data={"1": samples},
    )

    with pytest.raises(LapTelemetryUnavailableError, match="required"):
        get_lap_telemetry(session, "AAA", 7)
