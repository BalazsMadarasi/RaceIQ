# RaceIQ

RaceIQ is an interactive Formula 1 data analytics application built with Python and
FastF1 for exploring driver pace, lap-time evolution, and telemetry.

## Project Status

RaceIQ is actively under development. The current application provides a session-level
pace dashboard and a single-lap 3D telemetry explorer. Synchronized multi-driver 3D race
replay is planned but is not part of the current application.

## Features

- Select Formula 1 seasons, Grand Prix weekends, and their available sessions.
- Handle conventional and Sprint weekend formats from the FastF1 event schedule.
- Prepare lap and sector timing data for analysis.
- Filter structurally unsuitable laps from representative-lap analysis.
- Compare descriptive pace metrics across drivers.
- Explore interactive lap-time distributions and multi-driver lap-time evolution.
- Inspect an individual lap through an interactive 3D track and speed visualization.
- Cache FastF1 data locally and avoid loading telemetry on pages that do not require it.

## 3D Track & Telemetry Explorer

The Track & Telemetry Explorer renders a selected timed lap as an interactive 3D circuit.
The horizontal shape uses FastF1 `X` and `Y` position telemetry, while color represents
speed in km/h.

The vertical height is a normalized, visually scaled representation of speed—not physical
circuit elevation. FastF1 combines car and position streams sampled at different times, so
the merged lap telemetry can contain interpolated values. Telemetry availability and quality
vary by session, driver, and lap.

## Analytics Methodology

RaceIQ defines representative laps by excluding laps that:

- have no valid lap time;
- include a pit entry or pit exit;
- are explicitly marked inaccurate by FastF1; or
- are marked deleted.

No statistical outlier or track-status filtering is currently applied. Traffic, tire
condition and degradation, fuel load, safety-car or yellow-flag periods, weather, and
changing track conditions can affect the retained laps. The displayed fastest, median,
mean, and variability metrics are descriptive summaries, not isolated measurements of
driver performance. Qualifying summaries do not separate Q1, Q2, and Q3.

## Tech Stack

- Python 3.12
- FastF1
- Pandas and NumPy
- Plotly
- Streamlit
- pytest
- Ruff

## Architecture

```text
FastF1
  ↓
data loading and local caching
  ↓
processing
  ↓
analytics
  ↓
visualization
  ↓
Streamlit UI
```

- `src/raceiq/data` loads FastF1 schedules and sessions, prepares laps, and validates
  telemetry inputs.
- `src/raceiq/analytics` filters representative laps and calculates driver pace summaries.
- `src/raceiq/visualization` builds reusable Plotly pace and telemetry figures.
- `app` contains the Streamlit session overview and Track & Telemetry Explorer.

The package modules do not depend on Streamlit, keeping the deterministic processing and
visualization code testable outside the UI.

## Running Locally

Python 3.12 is required. From the repository root, create a virtual environment:

```text
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the project and development dependencies, then start Streamlit:

```text
python -m pip install -r requirements-dev.txt
streamlit run app/main.py
```

Initial FastF1 requests require network access and can take longer while the local cache is
populated.

## Quality Checks

```text
ruff check .
ruff format --check .
pytest
```

The unit tests use local fixtures and synthetic data rather than live FastF1 requests.

## Project Structure

```text
app/                      Streamlit entry point and pages
src/raceiq/data/          FastF1 access, lap preparation, telemetry validation
src/raceiq/analytics/     Representative-lap filtering and pace summaries
src/raceiq/visualization/ Plotly pace and 3D telemetry figures
tests/                    Deterministic unit tests
scripts/                  Smoke test and exploratory analysis
data/                     Ignored FastF1 cache and generated data
```

## Limitations

- Results depend on the availability and quality of upstream FastF1 data.
- Telemetry is not available for every session, driver, or lap.
- Current pace metrics are descriptive and do not control for race context.
- The application is actively developed and is not yet publicly deployed.

## Roadmap

- Synchronized multi-driver 3D race replay.
- Richer side-by-side driver telemetry comparisons.
- Strategy analysis with explicitly documented assumptions.
- Public deployment.

## Data Attribution

Formula 1 timing and telemetry data are accessed through
[FastF1](https://docs.fastf1.dev/). RaceIQ is an unofficial personal portfolio project and
is not affiliated with Formula 1.
