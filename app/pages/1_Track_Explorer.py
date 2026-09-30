import logging
from datetime import date

import fastf1
import pandas as pd
import streamlit as st
from fastf1.core import Session

from raceiq.data.fastf1_client import get_event_session_options, load_session
from raceiq.data.telemetry import (
    DriverTelemetryUnavailableError,
    LapTelemetryUnavailableError,
    SessionTelemetryUnavailableError,
    get_available_drivers,
    get_driver_lap_options,
    get_lap_telemetry,
    validate_session_telemetry,
)
from raceiq.visualization.track import plot_3d_speed_track, prepare_track_telemetry

DEFAULT_YEAR = 2024
DEFAULT_EVENT = "Italian Grand Prix"
DEFAULT_SESSION = "Qualifying"
FIRST_SUPPORTED_YEAR = 2018
FASTF1_VERSION = fastf1.__version__

LOGGER = logging.getLogger(__name__)


@st.cache_data(show_spinner=False, max_entries=8)
def load_track_event_options(year: int) -> dict[str, list[str]]:
    """Return cached events and sessions for the telemetry page."""
    return get_event_session_options(year)


@st.cache_resource(show_spinner=False, max_entries=2)
def load_track_session(
    year: int,
    event: str,
    session_type: str,
    fastf1_version: str,
) -> Session:
    """Load a telemetry-enabled session and retain it for lap changes."""
    session = load_session(
        year,
        event,
        session_type,
        telemetry=True,
        weather=False,
    )
    validate_session_telemetry(session)
    return session


@st.cache_data(show_spinner=False, max_entries=64)
def load_prepared_lap_telemetry(
    year: int,
    event: str,
    session_type: str,
    driver: str,
    lap_number: int,
    fastf1_version: str,
) -> pd.DataFrame:
    """Extract and prepare one selected lap's telemetry with explicit cache keys."""
    session = load_track_session(year, event, session_type, fastf1_version)
    telemetry = get_lap_telemetry(session, driver, lap_number)
    return prepare_track_telemetry(telemetry)


def format_lap_time(lap_time: pd.Timedelta) -> str:
    """Format a lap time for a selector or metric."""
    total_seconds = lap_time.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = total_seconds - minutes * 60
    return f"{minutes}:{seconds:06.3f}"


st.set_page_config(page_title="Track & Telemetry · RaceIQ", page_icon="🏁", layout="wide")

st.title("Track & Telemetry Explorer")
st.write(
    "Explore one timed lap as an interactive 3D circuit. Horizontal position comes from "
    "FastF1 position telemetry; height and color represent speed."
)

st.sidebar.header("Telemetry selection")
available_years = list(range(date.today().year, FIRST_SUPPORTED_YEAR - 1, -1))
selected_year = st.sidebar.selectbox(
    "Year",
    options=available_years,
    index=available_years.index(DEFAULT_YEAR),
    key="track_year",
)

try:
    with st.spinner(f"Loading the {selected_year} event schedule..."):
        event_options = load_track_event_options(selected_year)
except Exception:
    LOGGER.exception("Could not load the %s event schedule.", selected_year)
    st.error(f"The {selected_year} event schedule could not be loaded. Try again later.")
    st.stop()

if not event_options:
    st.warning(f"No Formula 1 events are available for {selected_year}.")
    st.stop()

available_events = list(event_options)
event_context_key = "_track_event_year"
if st.session_state.get(event_context_key) != selected_year:
    st.session_state["track_event"] = (
        DEFAULT_EVENT
        if selected_year == DEFAULT_YEAR and DEFAULT_EVENT in available_events
        else available_events[0]
    )
    st.session_state[event_context_key] = selected_year

selected_event = st.sidebar.selectbox(
    "Event / Grand Prix",
    options=available_events,
    key="track_event",
)
available_sessions = event_options.get(selected_event, [])
if not available_sessions:
    st.warning(f"No sessions are listed for the {selected_year} {selected_event}.")
    st.stop()

session_context = (selected_year, selected_event)
session_context_key = "_track_session_context"
if st.session_state.get(session_context_key) != session_context:
    if DEFAULT_SESSION in available_sessions:
        default_session = DEFAULT_SESSION
    elif "Race" in available_sessions:
        default_session = "Race"
    else:
        default_session = available_sessions[0]
    st.session_state["track_session"] = default_session
    st.session_state[session_context_key] = session_context

selected_session = st.sidebar.selectbox(
    "Session",
    options=available_sessions,
    key="track_session",
)

st.caption(f"{selected_year} · {selected_event} · {selected_session}")

try:
    with st.spinner("Loading telemetry-enabled session data..."):
        session = load_track_session(
            selected_year,
            selected_event,
            selected_session,
            FASTF1_VERSION,
        )
except SessionTelemetryUnavailableError:
    LOGGER.exception(
        "Telemetry unavailable for %s %s %s.",
        selected_year,
        selected_event,
        selected_session,
    )
    st.error(
        f"Telemetry is unavailable for the {selected_year} {selected_event} "
        f"{selected_session}. Try another session or season."
    )
    st.stop()
except Exception:
    LOGGER.exception(
        "Could not load %s %s %s.",
        selected_year,
        selected_event,
        selected_session,
    )
    st.error(
        f"The {selected_year} {selected_event} {selected_session} could not be loaded. "
        "Check your connection and try again."
    )
    st.stop()

available_drivers = get_available_drivers(session)
if not available_drivers:
    st.warning("No drivers with suitable timed laps are available for this session.")
    st.stop()

selected_driver = st.sidebar.selectbox(
    "Driver",
    options=available_drivers,
    key=f"track_driver::{selected_year}::{selected_event}::{selected_session}",
)
lap_options = get_driver_lap_options(session, selected_driver)
if lap_options.empty:
    st.warning(f"No timed, non-deleted laps are available for {selected_driver}.")
    st.stop()

lap_times = lap_options.set_index("LapNumber")["LapTime"].to_dict()
available_laps = lap_options["LapNumber"].tolist()
fastest_lap_number = int(lap_options.loc[lap_options["LapTime"].idxmin(), "LapNumber"])
lap_labels = {
    f"Lap {lap_number} — {format_lap_time(lap_times[lap_number])}": lap_number
    for lap_number in available_laps
}
fastest_lap_label = next(
    label for label, lap_number in lap_labels.items() if lap_number == fastest_lap_number
)

selected_lap_label = st.sidebar.selectbox(
    "Lap",
    options=list(lap_labels),
    index=list(lap_labels).index(fastest_lap_label),
    key=(f"track_lap::{selected_year}::{selected_event}::{selected_session}::{selected_driver}"),
)
selected_lap = lap_labels[selected_lap_label]
selected_lap_time = lap_times[selected_lap]

try:
    with st.spinner(f"Preparing {selected_driver}'s lap {selected_lap} telemetry..."):
        telemetry = load_prepared_lap_telemetry(
            selected_year,
            selected_event,
            selected_session,
            selected_driver,
            selected_lap,
            FASTF1_VERSION,
        )
        figure = plot_3d_speed_track(telemetry)
except SessionTelemetryUnavailableError:
    LOGGER.exception(
        "Session telemetry became unavailable for %s %s %s.",
        selected_year,
        selected_event,
        selected_session,
    )
    st.error(
        f"Telemetry is unavailable for the {selected_year} {selected_event} "
        f"{selected_session}. Try another session or season."
    )
    st.stop()
except DriverTelemetryUnavailableError:
    LOGGER.exception(
        "Driver telemetry unavailable for %s in %s %s %s.",
        selected_driver,
        selected_year,
        selected_event,
        selected_session,
    )
    st.error(
        f"Telemetry is unavailable for {selected_driver} in this session. "
        "Try another driver or session."
    )
    st.stop()
except LapTelemetryUnavailableError:
    LOGGER.exception(
        "Lap telemetry unavailable for %s lap %s.",
        selected_driver,
        selected_lap,
    )
    st.error(
        f"Lap {selected_lap} for {selected_driver} has incomplete or unavailable telemetry. "
        "Try another lap."
    )
    st.stop()
except ValueError:
    LOGGER.exception(
        "Lap telemetry could not be prepared for %s lap %s.",
        selected_driver,
        selected_lap,
    )
    st.error(
        f"Lap {selected_lap} for {selected_driver} contains too few usable telemetry "
        "samples for this visualization."
    )
    st.stop()
except Exception:
    LOGGER.exception(
        "Unexpected telemetry error for %s lap %s.",
        selected_driver,
        selected_lap,
    )
    st.error("The telemetry could not be prepared. Check your connection and try again.")
    st.stop()

lap_distance = telemetry["Distance"].max() - telemetry["Distance"].min()
metric_columns = st.columns(6)
metric_columns[0].metric("Driver", selected_driver)
metric_columns[1].metric("Lap", selected_lap)
metric_columns[2].metric("Lap time", format_lap_time(selected_lap_time))
metric_columns[3].metric("Maximum speed", f"{telemetry['Speed'].max():.1f} km/h")
metric_columns[4].metric("Minimum speed", f"{telemetry['Speed'].min():.1f} km/h")
metric_columns[5].metric("Approx. distance", f"{lap_distance / 1000:.3f} km")

st.header("3D speed profile")
st.caption("Raised height is visually scaled speed, not physical track elevation.")
st.plotly_chart(
    figure,
    width="stretch",
    config={"scrollZoom": True, "displaylogo": False},
)

st.header("Methodology and limitations")
st.markdown(
    """
- Circuit shape uses FastF1 `X` and `Y` position channels, converted from tenths of a
  metre and centered without changing the horizontal aspect ratio.
- The raised line's **height is normalized and visually scaled speed**, not physical track
  elevation. Color and hover values retain the actual speed in km/h.
- FastF1's `Lap.get_telemetry()` merges car and position streams, so some values may be
  interpolated and the source streams are not necessarily sampled at identical times.
- The chart deterministically limits plotting samples for responsiveness while retaining
  the beginning, end, and order of the lap.
- Telemetry availability and quality vary between sessions, drivers, and laps.
"""
)
