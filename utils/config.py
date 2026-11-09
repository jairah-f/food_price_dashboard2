"""Fixed research metadata and shared constants.

Nothing in this file is generated. METADATA holds the supplied dataset
coverage figures and PERIODS holds the study's period definitions.
"""
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"

# ---- Files that switch the dashboard from DEMO to real data -----------------
# Drop these files into /data and the matching part of the app stops using mock data.
WFP_CSV_PATH = DATA_DIR / "wfp_food_prices_philippines.csv"   # raw WFP file
FORECASTS_CSV_PATH = DATA_DIR / "forecasts.csv"               # model forecasts
METRICS_CSV_PATH = DATA_DIR / "model_metrics.csv"             # MAE / RMSE / MAPE

# ---- Fixed dataset coverage (supplied research metadata) --------------------
METADATA = {
    "Total Records": "210,339",
    "Commodities": "66",
    "Food Categories": "4",
    "Markets": "97",
    "Provinces": "78",
    "Regions": "17",
    "Study Period": "Jan 2016 – Jun 2026",
}
WHOLESALE_EXCLUDED = "2,615"

# ---- Pandemic periods -------------------------------------------------------
PERIODS = {
    "Pre-Pandemic": (pd.Timestamp("2016-01-01"), pd.Timestamp("2020-02-29")),
    "Pandemic": (pd.Timestamp("2020-03-01"), pd.Timestamp("2022-12-31")),
    "Post-Pandemic": (pd.Timestamp("2023-01-01"), pd.Timestamp("2026-06-30")),
}
PERIOD_ORDER = list(PERIODS)
PERIOD_RANGE_LABELS = {
    "Pre-Pandemic": "Jan 2016 – Feb 2020",
    "Pandemic": "Mar 2020 – Dec 2022",
    "Post-Pandemic": "Jan 2023 – Jun 2026",
}

# ---- Forecasting ------------------------------------------------------------
MODELS = ["Seasonal Naive", "SARIMA"]
HORIZONS = [3, 6, 9, 12]
# Placeholder eligibility rule: minimum monthly observations for a series to be forecast.
# TODO(REAL ANALYSIS): replace with the study's actual eligibility criteria.
MIN_OBS_FOR_FORECAST = 36

# Default selections (used only if present in the loaded data)
DEFAULT_COMMODITY = "Rice (Regular Milled)"

# ---- Palette ----------------------------------------------------------------
NAVY = "#1F3A5F"
GREEN = "#5B8C6A"
SLATE = "#8FA9C7"
SAND = "#C9B27C"
INK = "#1B2430"
MUTED = "#6B7684"
GRID = "#E6EAF0"
CATEGORY_COLORS = [NAVY, GREEN, SLATE, SAND, "#7C8B9A", "#A8C3A0"]
PERIOD_COLORS = {"Pre-Pandemic": SLATE, "Pandemic": NAVY, "Post-Pandemic": GREEN}
MODEL_COLORS = {"Seasonal Naive": SLATE, "SARIMA": GREEN}
