"""Plotly visualizations for exploring representative race pace."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_driver_pace_distribution(
    laps: pd.DataFrame,
    pace_summary: pd.DataFrame | None = None,
) -> go.Figure:
    """Return a driver lap-time box plot ordered by median pace."""
    if pace_summary is not None:
        driver_order = (
            pace_summary.sort_values("MedianLapSeconds")["Driver"].dropna().tolist()
        )
    else:
        driver_order = (
            laps.groupby("Driver")["LapTimeSeconds"].median().sort_values().index.tolist()
        )

    hover_columns = [
        column
        for column in ("LapNumber", "Team", "Compound", "TyreLife", "Stint")
        if column in laps.columns
    ]
    figure = px.box(
        laps,
        x="Driver",
        y="LapTimeSeconds",
        points="outliers",
        category_orders={"Driver": driver_order},
        hover_data=hover_columns,
        title="Representative Race-Lap Time Distribution by Driver",
    )
    figure.update_traces(marker={"opacity": 0.6, "size": 5})
    figure.update_layout(
        template="plotly_white",
        height=650,
        xaxis_title="Driver",
        yaxis_title="Lap time (seconds)",
        showlegend=False,
    )
    return figure


def plot_lap_time_evolution(
    laps: pd.DataFrame,
    drivers: list[str] | None = None,
) -> go.Figure:
    """Return lap times across the race for all or selected drivers."""
    driver_order = (
        list(dict.fromkeys(drivers))
        if drivers is not None
        else laps["Driver"].dropna().drop_duplicates().tolist()
    )
    plot_laps = laps.loc[laps["Driver"].isin(driver_order)].copy()
    plot_laps.sort_values(["Driver", "LapNumber"], kind="stable", inplace=True)

    hover_columns = [
        column
        for column in ("Team", "Compound", "TyreLife", "Stint")
        if column in plot_laps.columns
    ]
    figure = px.line(
        plot_laps,
        x="LapNumber",
        y="LapTimeSeconds",
        color="Driver",
        markers=True,
        category_orders={"Driver": driver_order},
        hover_data=hover_columns,
        title="Representative Lap-Time Evolution",
    )
    figure.update_traces(line={"width": 1.5}, marker={"size": 5})
    figure.update_layout(
        template="plotly_white",
        height=650,
        xaxis_title="Lap number",
        yaxis_title="Lap time (seconds)",
        legend_title_text="Driver",
        hovermode="x unified",
    )
    return figure
