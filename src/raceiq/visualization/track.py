"""Preparation and Plotly visualization for three-dimensional speed tracks."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

REQUIRED_TELEMETRY_COLUMNS = ("X", "Y", "Speed", "Distance")
MINIMUM_TELEMETRY_SAMPLES = 10
DEFAULT_MAX_SAMPLES = 800
DEFAULT_HEIGHT_SCALE = 0.18


def prepare_track_telemetry(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean telemetry while preserving speed and circuit shape."""
    missing_columns = [
        column for column in REQUIRED_TELEMETRY_COLUMNS if column not in telemetry.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Telemetry is missing required columns: {missing}.")

    prepared = telemetry.copy()
    for column in REQUIRED_TELEMETRY_COLUMNS:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

    prepared.replace([np.inf, -np.inf], np.nan, inplace=True)
    prepared.dropna(subset=REQUIRED_TELEMETRY_COLUMNS, inplace=True)
    prepared.sort_values("Distance", kind="stable", inplace=True)
    prepared.drop_duplicates(subset="Distance", keep="first", inplace=True)
    prepared.reset_index(drop=True, inplace=True)

    if len(prepared) < MINIMUM_TELEMETRY_SAMPLES:
        raise ValueError(f"Telemetry has fewer than {MINIMUM_TELEMETRY_SAMPLES} usable samples.")

    x_metres = prepared["X"] / 10.0
    y_metres = prepared["Y"] / 10.0
    prepared["PlotX"] = x_metres - (x_metres.min() + x_metres.max()) / 2
    prepared["PlotY"] = y_metres - (y_metres.min() + y_metres.max()) / 2
    return prepared


def downsample_telemetry(
    telemetry: pd.DataFrame,
    max_samples: int = DEFAULT_MAX_SAMPLES,
) -> pd.DataFrame:
    """Return evenly selected ordered samples, including both endpoints."""
    if max_samples < 2:
        raise ValueError("max_samples must be at least 2.")
    if len(telemetry) <= max_samples:
        return telemetry.copy()

    sample_indices = np.linspace(0, len(telemetry) - 1, num=max_samples, dtype=int)
    return telemetry.iloc[np.unique(sample_indices)].copy().reset_index(drop=True)


def plot_3d_speed_track(
    telemetry: pd.DataFrame,
    *,
    max_samples: int = DEFAULT_MAX_SAMPLES,
    height_scale: float = DEFAULT_HEIGHT_SCALE,
) -> go.Figure:
    """Return a 3D track whose scaled height and color represent actual speed."""
    if height_scale <= 0:
        raise ValueError("height_scale must be greater than zero.")

    prepared = prepare_track_telemetry(telemetry)
    plot_data = downsample_telemetry(prepared, max_samples=max_samples)

    horizontal_extent = max(
        float(np.ptp(prepared["PlotX"])),
        float(np.ptp(prepared["PlotY"])),
    )
    if horizontal_extent <= 0:
        raise ValueError("Telemetry does not contain a usable spatial trajectory.")

    speeds = plot_data["Speed"].to_numpy(dtype=float)
    speed_range = float(np.ptp(speeds))
    normalized_speed = (
        (speeds - speeds.min()) / speed_range if speed_range > 0 else np.zeros_like(speeds)
    )
    display_height = normalized_speed * horizontal_extent * height_scale
    base_height = np.zeros(len(plot_data))
    hover_data = np.column_stack((speeds, plot_data["Distance"].to_numpy(dtype=float)))

    figure = go.Figure()
    figure.add_trace(
        go.Scatter3d(
            x=plot_data["PlotX"],
            y=plot_data["PlotY"],
            z=base_height,
            mode="lines",
            line={"color": "rgba(155, 170, 195, 0.48)", "width": 6},
            hoverinfo="skip",
            name="Circuit outline",
        )
    )
    figure.add_trace(
        go.Scatter3d(
            x=plot_data["PlotX"],
            y=plot_data["PlotY"],
            z=display_height,
            mode="lines",
            line={
                "color": speeds,
                "colorscale": "Turbo",
                "cmin": float(speeds.min()),
                "cmax": float(speeds.max()),
                "colorbar": {
                    "title": {"text": "Speed (km/h)", "side": "top"},
                    "thickness": 14,
                    "len": 0.55,
                    "x": 0.98,
                    "y": 0.5,
                    "xanchor": "left",
                    "yanchor": "middle",
                },
                "width": 8,
            },
            customdata=hover_data,
            hovertemplate=(
                "Speed: %{customdata[0]:.1f} km/h<br>"
                "Distance: %{customdata[1]:.0f} m<extra></extra>"
            ),
            name="Speed profile",
        )
    )
    figure.add_trace(
        go.Scatter3d(
            x=[plot_data.loc[0, "PlotX"]],
            y=[plot_data.loc[0, "PlotY"]],
            z=[display_height[0]],
            mode="markers",
            marker={
                "color": "white",
                "line": {"color": "#111827", "width": 2},
                "size": 5,
                "symbol": "diamond",
            },
            hovertemplate="Lap start<extra></extra>",
            name="Lap start",
        )
    )
    figure.update_layout(
        template="plotly_dark",
        height=690,
        margin={"l": 0, "r": 48, "t": 4, "b": 0},
        paper_bgcolor="#080b12",
        scene={
            "bgcolor": "#080b12",
            "domain": {"x": [0, 0.94], "y": [0, 1]},
            "aspectmode": "data",
            "camera": {
                "eye": {"x": 1.35, "y": -1.55, "z": 1.0},
                "up": {"x": 0, "y": 0, "z": 1},
            },
            "xaxis": {
                "title": "",
                "showticklabels": False,
                "showgrid": False,
                "showbackground": False,
                "zeroline": False,
            },
            "yaxis": {
                "title": "",
                "showticklabels": False,
                "showgrid": False,
                "showbackground": False,
                "zeroline": False,
            },
            "zaxis": {
                "title": "",
                "showticklabels": False,
                "showgrid": False,
                "showbackground": False,
                "zeroline": False,
            },
        },
        showlegend=False,
    )
    return figure
