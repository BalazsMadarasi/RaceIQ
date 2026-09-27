import pandas as pd
import pytest

from raceiq.data.processing import prepare_laps


def test_prepare_laps_converts_timing_columns_to_seconds() -> None:
    laps = pd.DataFrame(
        {
            "LapTime": [pd.Timedelta(seconds=92.456)],
            "Sector1Time": [pd.Timedelta(seconds=30.1)],
            "Sector2Time": [pd.Timedelta(seconds=31.2)],
            "Sector3Time": [pd.Timedelta(seconds=31.156)],
        }
    )

    prepared = prepare_laps(laps)

    assert prepared.loc[0, "LapTimeSeconds"] == pytest.approx(92.456)
    assert prepared.loc[0, "Sector1TimeSeconds"] == pytest.approx(30.1)
    assert prepared.loc[0, "Sector2TimeSeconds"] == pytest.approx(31.2)
    assert prepared.loc[0, "Sector3TimeSeconds"] == pytest.approx(31.156)


def test_prepare_laps_preserves_missing_timing_values() -> None:
    laps = pd.DataFrame({"LapTime": pd.Series([pd.NaT], dtype="timedelta64[ns]")})

    prepared = prepare_laps(laps)

    assert pd.isna(prepared.loc[0, "LapTimeSeconds"])


def test_prepare_laps_does_not_mutate_input() -> None:
    laps = pd.DataFrame({"LapTime": [pd.Timedelta(seconds=90)]})
    original = laps.copy(deep=True)

    prepared = prepare_laps(laps)

    pd.testing.assert_frame_equal(laps, original)
    assert prepared is not laps
    assert "LapTimeSeconds" not in laps.columns


def test_prepare_laps_adds_pit_flags_from_timing_values() -> None:
    laps = pd.DataFrame(
        {
            "PitInTime": [pd.Timedelta(minutes=45), pd.NaT],
            "PitOutTime": [pd.NaT, pd.Timedelta(minutes=46)],
        }
    )

    prepared = prepare_laps(laps)

    assert prepared["IsPitInLap"].tolist() == [True, False]
    assert prepared["IsPitOutLap"].tolist() == [False, True]
