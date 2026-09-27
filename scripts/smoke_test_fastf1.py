"""Load one historical race and print a concise FastF1 dataset summary."""

from raceiq.data.fastf1_client import load_session
from raceiq.data.processing import prepare_laps

PREVIEW_COLUMNS = (
    "Driver",
    "LapNumber",
    "LapTime",
    "LapTimeSeconds",
    "Sector1TimeSeconds",
    "Sector2TimeSeconds",
    "Sector3TimeSeconds",
    "Stint",
    "Compound",
    "TyreLife",
    "IsPitInLap",
    "IsPitOutLap",
)


def main() -> None:
    """Run the FastF1 data-loading smoke test."""
    session = load_session(2024, "Italian Grand Prix", "Race")
    laps = prepare_laps(session.laps)

    event_name = session.event.get("EventName", "Unknown")
    event_date = session.event.get("EventDate", "Unknown")
    drivers = sorted(laps["Driver"].dropna().unique()) if "Driver" in laps.columns else []
    preview_columns = [column for column in PREVIEW_COLUMNS if column in laps.columns]

    print("FastF1 session loaded successfully")
    print(f"Event: {event_name}")
    print(f"Session: {session.name}")
    print(f"Event date: {event_date}")
    print(f"Lap rows: {len(laps)}")
    print(f"Drivers ({len(drivers)}): {', '.join(drivers)}")
    print(f"Preview columns: {', '.join(preview_columns)}")

    print("\nData quality:")
    if "LapTime" in laps.columns:
        print(f"Missing lap times: {laps['LapTime'].isna().sum()}")
    if "IsPitInLap" in laps.columns:
        print(f"Pit-in laps: {laps['IsPitInLap'].sum()}")
    if "IsPitOutLap" in laps.columns:
        print(f"Pit-out laps: {laps['IsPitOutLap'].sum()}")
    if "IsAccurate" in laps.columns:
        print(f"Accurate laps: {laps['IsAccurate'].eq(True).sum()}")
        print(f"Inaccurate laps: {laps['IsAccurate'].eq(False).sum()}")
    if "Deleted" in laps.columns:
        print(f"Deleted laps: {laps['Deleted'].eq(True).sum()}")
    if "TrackStatus" in laps.columns:
        print(f"Track statuses: {laps['TrackStatus'].value_counts().sort_index().to_dict()}")

    if preview_columns and not laps.empty:
        print("\nFirst five laps:")
        print(laps.loc[:, preview_columns].head().to_string(index=False))
    else:
        print("No lap data is available for preview.")


if __name__ == "__main__":
    main()
