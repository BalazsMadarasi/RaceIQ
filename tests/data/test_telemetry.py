import pandas as pd

from raceiq.data.telemetry import get_available_drivers, get_driver_lap_options


class FakeSession:
    def __init__(self, laps: pd.DataFrame) -> None:
        self.laps = laps


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
