import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from raceiq.visualization.track import (
    downsample_telemetry,
    plot_3d_speed_track,
    prepare_track_telemetry,
)


def make_telemetry(sample_count: int = 20) -> pd.DataFrame:
    distance = np.linspace(0, 5000, sample_count)
    return pd.DataFrame(
        {
            "X": distance * 2,
            "Y": np.sin(np.linspace(0, 2 * np.pi, sample_count)) * 1000,
            "Speed": np.linspace(100, 300, sample_count),
            "Distance": distance,
        }
    )


def test_prepare_track_telemetry_validates_required_columns() -> None:
    telemetry = make_telemetry().drop(columns="Speed")

    with pytest.raises(ValueError, match="Speed"):
        prepare_track_telemetry(telemetry)


def test_prepare_track_telemetry_cleans_and_rejects_insufficient_data() -> None:
    telemetry = make_telemetry(12)
    telemetry.loc[0, "Speed"] = np.nan
    telemetry.loc[1, "X"] = np.inf
    telemetry.loc[3, "Distance"] = telemetry.loc[2, "Distance"]

    with pytest.raises(ValueError, match="fewer than 10"):
        prepare_track_telemetry(telemetry)


def test_downsampling_preserves_order_endpoints_and_input() -> None:
    telemetry = make_telemetry(20)
    original = telemetry.copy(deep=True)

    sampled = downsample_telemetry(telemetry, max_samples=6)

    assert len(sampled) == 6
    assert sampled["Distance"].is_monotonic_increasing
    assert sampled.iloc[0]["Distance"] == telemetry.iloc[0]["Distance"]
    assert sampled.iloc[-1]["Distance"] == telemetry.iloc[-1]["Distance"]
    pd.testing.assert_frame_equal(telemetry, original)


def test_plot_3d_speed_track_returns_spatial_speed_figure_without_mutation() -> None:
    telemetry = make_telemetry(20)
    original = telemetry.copy(deep=True)

    figure = plot_3d_speed_track(telemetry, max_samples=20)

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 3
    assert list(figure.data[1].x) == pytest.approx(
        prepare_track_telemetry(telemetry)["PlotX"].tolist()
    )
    assert figure.data[1].z[0] < figure.data[1].z[-1]
    pd.testing.assert_frame_equal(telemetry, original)
