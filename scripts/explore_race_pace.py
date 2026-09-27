"""Explore representative race-pace distributions with interactive Plotly charts."""

from raceiq.analytics.pace import filter_representative_laps, summarize_driver_pace
from raceiq.data.fastf1_client import load_session
from raceiq.data.processing import prepare_laps
from raceiq.visualization.pace import plot_driver_pace_distribution, plot_lap_time_evolution

SELECTED_DRIVERS = ["PIA", "NOR", "VER", "HAM", "LEC"]


def main() -> None:
    """Load the Italian Grand Prix and open exploratory pace charts."""
    session = load_session(2024, "Italian Grand Prix", "Race")
    prepared_laps = prepare_laps(session.laps)
    representative_laps = filter_representative_laps(prepared_laps)
    pace_summary = summarize_driver_pace(prepared_laps)

    distributions = (
        representative_laps.groupby("Driver")["LapTimeSeconds"]
        .agg(
            RepresentativeLapCount="count",
            MinimumLapSeconds="min",
            Q1LapSeconds=lambda values: values.quantile(0.25),
            MedianLapSeconds="median",
            Q3LapSeconds=lambda values: values.quantile(0.75),
            MaximumLapSeconds="max",
        )
        .reset_index()
    )
    distributions["MaximumMinusMedianSeconds"] = (
        distributions["MaximumLapSeconds"] - distributions["MedianLapSeconds"]
    )
    distributions.sort_values("MedianLapSeconds", inplace=True)

    print(f"Raw laps: {len(prepared_laps)}")
    print(f"Representative laps: {len(representative_laps)}")
    print(f"Drivers: {representative_laps['Driver'].nunique()}")
    print("\nPace summary:")
    print(pace_summary.round(3).to_string(index=False))
    print("\nDistribution diagnostics (no additional filtering applied):")
    print(distributions.round(3).to_string(index=False))

    distribution_figure = plot_driver_pace_distribution(representative_laps, pace_summary)
    evolution_figure = plot_lap_time_evolution(representative_laps, SELECTED_DRIVERS)
    distribution_figure.show()
    evolution_figure.show()


if __name__ == "__main__":
    main()
