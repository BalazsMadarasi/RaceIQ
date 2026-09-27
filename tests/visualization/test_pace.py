import pandas as pd
import plotly.graph_objects as go

from raceiq.visualization.pace import plot_driver_pace_distribution, plot_lap_time_evolution


def test_distribution_returns_figure_in_median_order_without_mutation() -> None:
    laps = pd.DataFrame(
        {
            "Driver": ["AAA", "AAA", "BBB", "BBB"],
            "LapTimeSeconds": [91.0, 93.0, 88.0, 90.0],
        }
    )
    original = laps.copy(deep=True)
    pace_summary = pd.DataFrame(
        {"Driver": ["AAA", "BBB"], "MedianLapSeconds": [92.0, 89.0]}
    )

    figure = plot_driver_pace_distribution(laps, pace_summary)

    assert isinstance(figure, go.Figure)
    assert tuple(figure.layout.xaxis.categoryarray) == ("BBB", "AAA")
    pd.testing.assert_frame_equal(laps, original)


def test_evolution_returns_figure_with_each_driver_ordered_by_lap() -> None:
    laps = pd.DataFrame(
        {
            "Driver": ["AAA", "BBB", "AAA", "BBB"],
            "LapNumber": [2, 2, 1, 1],
            "LapTimeSeconds": [92.0, 90.0, 91.0, 89.0],
        }
    )
    original = laps.copy(deep=True)

    figure = plot_lap_time_evolution(laps, drivers=["AAA"])

    assert isinstance(figure, go.Figure)
    assert list(figure.data[0].x) == [1, 2]
    pd.testing.assert_frame_equal(laps, original)
