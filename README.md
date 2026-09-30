# RaceIQ

RaceIQ is a Formula 1 performance analytics project built with a reusable Python package
and an interactive Streamlit dashboard. Its first dashboard explores historical Formula 1
sessions using data loaded through FastF1.

> **Status:** Early development. The selectable Session Overview MVP is functional;
> additional analysis areas remain planned.

## Current functionality

- FastF1 session loading with a local disk cache
- Lap preparation with numeric lap and sector times
- Conservative representative-lap filtering
- Per-driver fastest, median, mean, and standard-deviation pace summaries
- Plotly pace-distribution and lap-time-evolution visualizations
- Selectable seasons and Grands Prix with chronologically ordered available sessions
- Streamlit Session Overview with KPI cards, a pace table, charts, and driver selection
- Interactive Track & Telemetry Explorer for individual driver laps

Session choices come from each FastF1 event schedule, including the historical Sprint
Shootout and Sprint Qualifying names where applicable. Race and Sprint dashboards distinguish
the completed lap count from the total number of individual driver-lap records. Other session
types show driver-lap counts without presenting a race-length metric.

The same conservative lap preparation is currently used across session types. Qualifying
views are descriptive and do not yet separate Q1, Q2, and Q3 or model changing track
conditions.

## Track & Telemetry Explorer

Open **Track & Telemetry Explorer** from Streamlit's page navigation. Select a season,
Grand Prix, session, driver, and timed non-deleted lap to view an interactive 3D circuit
generated from real FastF1 position and speed telemetry.

The horizontal circuit shape uses FastF1's `X` and `Y` channels. The visualization's
vertical height is a normalized, visually scaled speed profile—not physical elevation.
Color and hover values retain speed in km/h. FastF1's merged lap telemetry can contain
interpolated samples because car and position data are recorded separately.

Telemetry-enabled sessions are loaded only on this page and retained in a small in-memory
cache. Individual prepared laps are cached separately. Initial loads can take longer and
require network access; telemetry may be incomplete or unavailable for some historical or
future sessions.

Representative laps exclude missing lap times, pit-in and pit-out laps, explicitly
inaccurate laps, and deleted laps. No statistical outlier or `TrackStatus` filtering is
currently applied.

## Planned features

- Driver comparison
- Telemetry analysis
- Strategy analysis
- Season trends

## Tech stack

- Python 3.12
- FastF1, pandas, and NumPy
- Plotly and Streamlit
- pytest and Ruff

## Local development

Create and activate a virtual environment, then install the runtime and development
dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Start the Session Overview dashboard from the repository root:

```powershell
streamlit run app/main.py
```

Run the project checks with:

```powershell
ruff check .
ruff format --check .
pytest
```

## Repository structure

```text
app/                      Streamlit application entry point
src/raceiq/data/          FastF1 loading and lap preparation
src/raceiq/analytics/     Race-pace filtering and summaries
src/raceiq/visualization/ Reusable Plotly figures
tests/                    Unit tests
scripts/                  Smoke tests and exploratory tools
data/                     Ignored FastF1 cache and generated datasets
```

RaceIQ uses Formula 1 data made available through
[FastF1](https://docs.fastf1.dev/). Users of the project are responsible for following
the data provider's terms and applicable usage policies.
