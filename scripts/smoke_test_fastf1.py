"""Load one historical race and print a concise FastF1 dataset summary."""

from raceiq.data.fastf1_client import load_session

PREVIEW_COLUMNS = (
    "Driver",
    "LapNumber",
    "LapTime",
    "Stint",
    "Compound",
    "TyreLife",
    "Team",
)


def main() -> None:
    """Run the FastF1 data-loading smoke test."""
    session = load_session(2024, "Italian Grand Prix", "Race")
    laps = session.laps

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

    if preview_columns and not laps.empty:
        print("\nFirst five laps:")
        print(laps.loc[:, preview_columns].head().to_string(index=False))
    else:
        print("No lap data is available for preview.")


if __name__ == "__main__":
    main()
