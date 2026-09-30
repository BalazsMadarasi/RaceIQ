from datetime import date

import pandas as pd
import streamlit as st

from raceiq.analytics.pace import filter_representative_laps, summarize_driver_pace
from raceiq.data.fastf1_client import get_event_session_options, load_session
from raceiq.data.processing import get_recorded_lap_count, prepare_laps
from raceiq.visualization.pace import plot_driver_pace_distribution, plot_lap_time_evolution

DEFAULT_YEAR = 2024
DEFAULT_EVENT = "Italian Grand Prix"
DEFAULT_SESSION_TYPE = "Race"
FIRST_SUPPORTED_YEAR = 2018
RACE_LENGTH_SESSION_TYPES = {"Race", "Sprint"}
QUALIFYING_SESSION_TYPES = {"Qualifying", "Sprint Qualifying", "Sprint Shootout"}


@st.cache_data(show_spinner=False)
def load_event_options(year: int) -> dict[str, list[str]]:
    """Return cached events and chronological session names for a season."""
    return get_event_session_options(year)


@st.cache_data(show_spinner=False)
def load_dashboard_data(
    year: int,
    event: str,
    session_type: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load and prepare a selected historical session for the dashboard."""
    session = load_session(
        year,
        event,
        session_type,
        telemetry=False,
        weather=False,
    )
    prepared_laps = prepare_laps(session.laps)
    representative_laps = filter_representative_laps(prepared_laps)
    pace_summary = summarize_driver_pace(prepared_laps)
    return prepared_laps, representative_laps, pace_summary


st.set_page_config(page_title="RaceIQ", page_icon="🏁", layout="wide")

st.title("RaceIQ")
st.subheader("Formula 1 Performance Analytics")
st.header("Session Overview")
st.write(
    "Explore structurally representative laps and descriptive driver pace for a selected "
    "historical session."
)

st.sidebar.header("Session selection")
available_years = list(range(date.today().year, FIRST_SUPPORTED_YEAR - 1, -1))
selected_year = st.sidebar.selectbox(
    "Year",
    options=available_years,
    index=available_years.index(DEFAULT_YEAR),
    key="selected_year",
)

try:
    with st.spinner(f"Loading the {selected_year} event schedule..."):
        event_options = load_event_options(selected_year)
except Exception as error:
    st.error(f"The {selected_year} event schedule could not be loaded. Try again later.")
    st.caption(f"Technical details: {error}")
    st.stop()

if not event_options:
    st.warning(f"No Formula 1 events are available for {selected_year}.")
    st.stop()

available_events = list(event_options)
event_context_key = "_event_selection_year"
if st.session_state.get(event_context_key) != selected_year:
    st.session_state["selected_event"] = (
        DEFAULT_EVENT
        if selected_year == DEFAULT_YEAR and DEFAULT_EVENT in available_events
        else available_events[0]
    )
    st.session_state[event_context_key] = selected_year

selected_event = st.sidebar.selectbox(
    "Event / Grand Prix",
    options=available_events,
    key="selected_event",
)
available_sessions = event_options.get(selected_event, [])
if not available_sessions:
    st.warning(f"No sessions are listed for the {selected_year} {selected_event}.")
    st.stop()

session_context = (selected_year, selected_event)
session_context_key = "_session_selection_context"
if st.session_state.get(session_context_key) != session_context:
    st.session_state["selected_session_type"] = (
        DEFAULT_SESSION_TYPE
        if DEFAULT_SESSION_TYPE in available_sessions
        else available_sessions[0]
    )
    st.session_state[session_context_key] = session_context

selected_session_type = st.sidebar.selectbox(
    "Session type",
    options=available_sessions,
    key="selected_session_type",
)

st.caption(f"{selected_year} · {selected_event} · {selected_session_type}")

try:
    with st.spinner(f"Loading {selected_event} — {selected_session_type}..."):
        prepared_laps, representative_laps, pace_summary = load_dashboard_data(
            selected_year,
            selected_event,
            selected_session_type,
        )
except Exception as error:
    st.error(
        f"{selected_session_type} data is unavailable for the {selected_year} "
        f"{selected_event}, or it could not be loaded. Choose another selection or try again."
    )
    st.caption(f"Technical details: {error}")
    st.stop()

raw_lap_count = len(prepared_laps)
representative_lap_count = len(representative_laps)
excluded_lap_count = raw_lap_count - representative_lap_count
driver_count = prepared_laps["Driver"].nunique()

metric_columns = st.columns(4)
if selected_session_type in RACE_LENGTH_SESSION_TYPES:
    recorded_lap_count = get_recorded_lap_count(prepared_laps)
    lap_metric_label = "Sprint laps" if selected_session_type == "Sprint" else "Race laps"
    metric_columns[0].metric(
        lap_metric_label,
        recorded_lap_count if recorded_lap_count is not None else "Unavailable",
    )
    metric_columns[1].metric("Drivers", driver_count)
    metric_columns[2].metric("Representative driver-laps", representative_lap_count)
    metric_columns[3].metric("Excluded driver-laps", excluded_lap_count)
    st.caption(f"Raw driver-lap records: {raw_lap_count}")
else:
    metric_columns[0].metric("Raw driver-laps", raw_lap_count)
    metric_columns[1].metric("Drivers", driver_count)
    metric_columns[2].metric("Representative driver-laps", representative_lap_count)
    metric_columns[3].metric("Excluded driver-laps", excluded_lap_count)

if selected_session_type in QUALIFYING_SESSION_TYPES:
    st.info(
        "Median lap time is descriptive across the selected session. It does not separate "
        "Q1, Q2, and Q3 or directly measure qualifying performance."
    )

st.header("Driver pace summary")
display_summary = pace_summary.rename(
    columns={
        "RepresentativeLapCount": "Representative laps",
        "FastestLapSeconds": "Fastest lap (s)",
        "MedianLapSeconds": "Median lap (s)",
        "MeanLapSeconds": "Mean lap (s)",
        "LapTimeStdSeconds": "Lap-time standard deviation (s)",
    }
)
st.dataframe(
    display_summary,
    hide_index=True,
    width="stretch",
    column_config={
        "Representative laps": st.column_config.NumberColumn(format="%d"),
        "Fastest lap (s)": st.column_config.NumberColumn(format="%.3f"),
        "Median lap (s)": st.column_config.NumberColumn(format="%.3f"),
        "Mean lap (s)": st.column_config.NumberColumn(format="%.3f"),
        "Lap-time standard deviation (s)": st.column_config.NumberColumn(format="%.3f"),
    },
)

st.header("Driver pace distributions")
st.write("Box plots show the spread of representative lap times for every driver.")
distribution_figure = plot_driver_pace_distribution(representative_laps, pace_summary)
st.plotly_chart(distribution_figure, width="stretch")

st.header("Lap-time evolution")
available_drivers = pace_summary["Driver"].tolist()
driver_context = (selected_year, selected_event, selected_session_type)
driver_context_key = "_driver_selection_context"
if st.session_state.get(driver_context_key) != driver_context:
    st.session_state["selected_drivers"] = available_drivers[:5]
    st.session_state[driver_context_key] = driver_context

selected_drivers = st.multiselect(
    "Drivers",
    options=available_drivers,
    key="selected_drivers",
    help="Select one or more drivers to compare their representative laps across the session.",
)
if selected_drivers:
    evolution_figure = plot_lap_time_evolution(representative_laps, selected_drivers)
    st.plotly_chart(evolution_figure, width="stretch")
else:
    st.info("Select at least one driver to display lap-time evolution.")

st.header("Methodology and limitations")
st.markdown(
    """
Representative laps currently exclude:

- laps with missing lap times;
- pit-in and pit-out laps;
- laps explicitly marked inaccurate by FastF1;
- deleted laps.

The current methodology does **not** correct for session-start conditions, safety cars or
yellow flags, traffic, fuel load, tire degradation, changing track conditions, or other
performance outliers. Median lap time is a descriptive summary of the retained laps, not
an isolated measurement of underlying driver performance.
"""
)
