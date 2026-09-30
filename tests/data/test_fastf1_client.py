import pandas as pd
import pytest

from raceiq.data import fastf1_client


def test_get_event_names_uses_non_testing_schedule(monkeypatch) -> None:
    calls = []

    def fake_get_event_schedule(year: int, *, include_testing: bool) -> pd.DataFrame:
        calls.append((year, include_testing))
        return pd.DataFrame({"EventName": ["Bahrain Grand Prix", "Saudi Arabian Grand Prix", None]})

    monkeypatch.setattr(fastf1_client, "enable_fastf1_cache", lambda: None)
    monkeypatch.setattr(fastf1_client.fastf1, "get_event_schedule", fake_get_event_schedule)

    event_names = fastf1_client.get_event_names(2024)

    assert event_names == ["Bahrain Grand Prix", "Saudi Arabian Grand Prix"]
    assert calls == [(2024, False)]


@pytest.mark.parametrize(
    ("sessions", "expected"),
    [
        (
            ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"],
            ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"],
        ),
        (
            ["Practice 1", "Qualifying", "Sprint Shootout", "Sprint", "Race"],
            ["Practice 1", "Qualifying", "Sprint Shootout", "Sprint", "Race"],
        ),
        (
            ["Practice 1", "Sprint Qualifying", "Sprint", "Qualifying", "Race"],
            ["Practice 1", "Sprint Qualifying", "Sprint", "Qualifying", "Race"],
        ),
    ],
    ids=["conventional", "2023-sprint", "2024-sprint"],
)
def test_get_event_session_options_preserves_schedule_order(
    monkeypatch,
    sessions: list[str],
    expected: list[str],
) -> None:
    schedule_row = {"EventName": "Example Grand Prix"}
    schedule_row.update(
        {f"Session{number}": session for number, session in enumerate(sessions, start=1)}
    )
    schedule = pd.DataFrame([schedule_row])
    monkeypatch.setattr(fastf1_client, "get_event_schedule", lambda year: schedule)

    options = fastf1_client.get_event_session_options(2024)

    assert options == {"Example Grand Prix": expected}
