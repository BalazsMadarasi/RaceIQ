"""Load one historical race and print a concise FastF1 dataset summary."""

from raceiq.analytics.pace import filter_representative_laps, summarize_driver_pace
from raceiq.data.fastf1_client import load_session
from raceiq.data.processing import prepare_laps


def main() -> None:
    """Run the FastF1 data-loading smoke test."""
    session = load_session(2024, "Italian Grand Prix", "Race")
    laps = prepare_laps(session.laps)
    representative_laps = filter_representative_laps(laps)
    pace_summary = summarize_driver_pace(laps)

    event_name = session.event.get("EventName", "Unknown")
    event_date = session.event.get("EventDate", "Unknown")
    drivers = sorted(laps["Driver"].dropna().unique()) if "Driver" in laps.columns else []

    print("FastF1 session loaded successfully")
    print(f"Event: {event_name}")
    print(f"Session: {session.name}")
    print(f"Event date: {event_date}")
    print(f"Drivers ({len(drivers)}): {', '.join(drivers)}")
    print(f"Raw laps: {len(laps)}")
    print(f"Representative laps: {len(representative_laps)}")
    print(f"Excluded laps: {len(laps) - len(representative_laps)}")

    print("\nExclusion diagnostics (categories may overlap):")
    print(f"Missing lap times: {laps['LapTimeSeconds'].isna().sum()}")
    if "IsPitInLap" in laps.columns:
        print(f"Pit-in laps: {laps['IsPitInLap'].sum()}")
    if "IsPitOutLap" in laps.columns:
        print(f"Pit-out laps: {laps['IsPitOutLap'].sum()}")
    if "IsAccurate" in laps.columns:
        print(f"Accurate laps: {laps['IsAccurate'].eq(True).sum()}")
        print(f"Inaccurate laps: {laps['IsAccurate'].eq(False).sum()}")
    if "Deleted" in laps.columns:
        print(f"Deleted laps: {laps['Deleted'].eq(True).sum()}")

    print("\nDriver pace summary:")
    print(pace_summary.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
