# RaceIQ

RaceIQ is an interactive Formula 1 performance analytics dashboard for exploring
race pace, driver performance, telemetry, tire strategy, and season-level trends.
It is built as a portfolio project with a reusable Python analytics package and a
Streamlit interface.

> **Status:** Early development. The project foundation is in place; analytics
> and dashboard features have not been implemented yet.

## Planned features

- Race overview
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

Create and activate a virtual environment, then install all runtime and
development dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Start the application from the repository root:

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
app/                 Streamlit application entry point and pages
src/raceiq/          Reusable data, analytics, and visualization package
tests/               Automated tests
data/                Local cache and generated datasets (not committed)
notebooks/           Exploratory notebooks
scripts/             Project utility scripts
assets/screenshots/  Project screenshots
```

RaceIQ uses Formula 1 data made available through
[FastF1](https://docs.fastf1.dev/). Users of the project are responsible for
following the data provider's terms and applicable usage policies.
