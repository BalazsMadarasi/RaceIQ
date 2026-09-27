import pandas as pd
import pytest

from raceiq.analytics.pace import filter_representative_laps, summarize_driver_pace


def test_filter_representative_laps_excludes_structurally_unsuitable_laps() -> None:
    laps = pd.DataFrame(
        {
            "LapTimeSeconds": [90.0, 91.0, 92.0, 93.0, 94.0, None, 96.0],
            "IsPitInLap": [False, True, False, False, False, False, pd.NA],
            "IsPitOutLap": [False, False, True, False, False, False, pd.NA],
            "IsAccurate": [True, True, True, False, True, True, pd.NA],
            "Deleted": [False, False, False, False, True, False, pd.NA],
        }
    )
    original = laps.copy(deep=True)

    representative = filter_representative_laps(laps)

    assert representative.index.tolist() == [0, 6]
    pd.testing.assert_frame_equal(laps, original)


def test_filter_representative_laps_allows_missing_optional_columns() -> None:
    laps = pd.DataFrame(
        {
            "LapTimeSeconds": [90.0, None, 92.0],
            "IsPitInLap": [False, False, True],
        }
    )

    representative = filter_representative_laps(laps)

    assert representative["LapTimeSeconds"].tolist() == [90.0]


def test_summarize_driver_pace_calculates_metrics_and_orders_by_median() -> None:
    laps = pd.DataFrame(
        {
            "Driver": ["AAA", "AAA", "AAA", "BBB", "BBB", "BBB"],
            "Team": ["Alpha"] * 3 + ["Beta"] * 3,
            "LapTimeSeconds": [90.0, 92.0, 94.0, 89.0, 90.0, 91.0],
        }
    )

    summary = summarize_driver_pace(laps)

    assert summary["Driver"].tolist() == ["BBB", "AAA"]
    by_driver = summary.set_index("Driver")
    assert by_driver.loc["AAA", "Team"] == "Alpha"
    assert by_driver.loc["AAA", "RepresentativeLapCount"] == 3
    assert by_driver.loc["AAA", "FastestLapSeconds"] == pytest.approx(90.0)
    assert by_driver.loc["AAA", "MedianLapSeconds"] == pytest.approx(92.0)
    assert by_driver.loc["AAA", "MeanLapSeconds"] == pytest.approx(92.0)
    assert by_driver.loc["AAA", "LapTimeStdSeconds"] == pytest.approx(2.0)
    assert by_driver.loc["BBB", "LapTimeStdSeconds"] == pytest.approx(1.0)


def test_summarize_driver_pace_handles_missing_team_column() -> None:
    laps = pd.DataFrame({"Driver": ["AAA", "AAA"], "LapTimeSeconds": [90.0, 92.0]})

    summary = summarize_driver_pace(laps)

    assert "Team" not in summary.columns
    assert summary.loc[0, "RepresentativeLapCount"] == 2
