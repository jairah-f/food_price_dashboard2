"""Analysis layer: summaries, period comparison, forecasts, evaluation metrics.

No Streamlit code here. Functions marked TODO(REAL ANALYSIS) are the places to
plug in the finished study outputs. Until then they fall back to mock_data.
"""
import numpy as np
import pandas as pd

from .config import (FORECASTS_CSV_PATH, METRICS_CSV_PATH, MIN_OBS_FOR_FORECAST,
                     PERIOD_ORDER, PERIODS)
from . import mock_data


# --------------------------------------------------------------------------- #
# Historical helpers
# --------------------------------------------------------------------------- #
def monthly_series(df: pd.DataFrame) -> pd.DataFrame:
    """Mean price per date across whatever rows are passed in -> [date, price]."""
    if df.empty:
        return pd.DataFrame(columns=["date", "price"])
    out = df.groupby("date", as_index=False)["price_php"].mean()
    return out.rename(columns={"price_php": "price"}).sort_values("date").reset_index(drop=True)


def historical_summary(series: pd.DataFrame) -> dict:
    """Average / min / max / % change for a [date, price] series."""
    if series.empty:
        return {}
    s = series.sort_values("date")
    first, last = float(s["price"].iloc[0]), float(s["price"].iloc[-1])
    i_min, i_max = s["price"].idxmin(), s["price"].idxmax()
    return {
        "avg": float(s["price"].mean()),
        "min": float(s.loc[i_min, "price"]), "min_date": s.loc[i_min, "date"],
        "max": float(s.loc[i_max, "price"]), "max_date": s.loc[i_max, "date"],
        "first": first, "last": last,
        "pct_change": (last / first - 1) * 100 if first else np.nan,
        "n": len(s),
    }


def category_series(df: pd.DataFrame, mode: str = "Index") -> pd.DataFrame:
    """Category trend lines -> [date, category, value].

    mode 'Index': each commodity is rescaled to 100 at its first observation in the
    range, then averaged within the category (avoids mixing PHP/kg and PHP/unit).
    mode 'Average price': plain mean PHP price per category.
    """
    if df.empty:
        return pd.DataFrame(columns=["date", "category", "value"])
    if mode == "Average price":
        out = df.groupby(["date", "category"], as_index=False)["price_php"].mean()
        return out.rename(columns={"price_php": "value"})
    m = df.groupby(["date", "category", "commodity"], as_index=False)["price_php"].mean()
    m = m.sort_values("date")
    m["value"] = m["price_php"] / m.groupby("commodity")["price_php"].transform("first") * 100
    return m.groupby(["date", "category"], as_index=False)["value"].mean()


# --------------------------------------------------------------------------- #
# Pandemic-period comparison
# --------------------------------------------------------------------------- #
def assign_period(dates) -> pd.Series:
    d = pd.to_datetime(pd.Series(dates))
    conds = [(d >= s) & (d <= e) for s, e in PERIODS.values()]
    return pd.Series(np.select(conds, PERIOD_ORDER, default=""), index=d.index).replace("", np.nan)


def period_availability(df: pd.DataFrame) -> dict:
    """Observation count per period. TODO(REAL ANALYSIS): extend to per-series checks."""
    p = assign_period(df["date"]) if len(df) else pd.Series(dtype=object)
    counts = p.value_counts()
    return {k: int(counts.get(k, 0)) for k in PERIOD_ORDER}


def period_summary(df: pd.DataFrame, periods=None) -> pd.DataFrame:
    """Average price and observation count per period -> [period, avg_price, n_obs]."""
    periods = periods or PERIOD_ORDER
    d = df.assign(period=assign_period(df["date"])) if len(df) else df.assign(period=[])
    g = d.dropna(subset=["period"]).groupby("period")["price_php"].agg(avg_price="mean", n_obs="size")
    out = g.reindex(periods).rename_axis("period").reset_index()
    out["n_obs"] = out["n_obs"].fillna(0).astype(int)
    return out


def period_changes(summary: pd.DataFrame) -> pd.DataFrame:
    """% change between period averages -> [comparison, pct_change]. Skips missing periods."""
    avg = summary.set_index("period")["avg_price"].dropna()
    pairs = [("Pre-Pandemic", "Pandemic"), ("Pandemic", "Post-Pandemic"),
             ("Pre-Pandemic", "Post-Pandemic")]
    rows = [{"comparison": f"{a} → {b}", "pct_change": (avg[b] / avg[a] - 1) * 100}
            for a, b in pairs if a in avg.index and b in avg.index and avg[a]]
    return pd.DataFrame(rows, columns=["comparison", "pct_change"])


def regional_period_summary(df: pd.DataFrame, periods=None) -> pd.DataFrame:
    """Average price by region and period -> [region, period, avg_price]."""
    periods = periods or PERIOD_ORDER
    if df.empty:
        return pd.DataFrame(columns=["region", "period", "avg_price"])
    d = df.assign(period=assign_period(df["date"])).dropna(subset=["period"])
    d = d[d["period"].isin(periods)]
    out = d.groupby(["region", "period"], as_index=False)["price_php"].mean()
    return out.rename(columns={"price_php": "avg_price"})


# --------------------------------------------------------------------------- #
# Forecasting  (TODO(REAL ANALYSIS): connect the study's forecast outputs)
# --------------------------------------------------------------------------- #
def is_eligible_series(series: pd.DataFrame) -> bool:
    """Placeholder eligibility check for forecasting."""
    return len(series) >= MIN_OBS_FOR_FORECAST


def forecast_seasonal_naive(series, horizon, commodity, market) -> pd.DataFrame:
    """PLACEHOLDER. TODO(REAL ANALYSIS): return the Seasonal Naive forecast.
    Expected columns: date, forecast, lower, upper, actual, segment."""
    return mock_data.mock_forecast(series, "Seasonal Naive", horizon, f"{commodity}|{market}")


def forecast_sarima(series, horizon, commodity, market) -> pd.DataFrame:
    """PLACEHOLDER. TODO(REAL ANALYSIS): return the SARIMA forecast (same columns)."""
    return mock_data.mock_forecast(series, "SARIMA", horizon, f"{commodity}|{market}")


def _precomputed_forecast(commodity, market, model, horizon):
    """Use data/forecasts.csv when present.
    Columns: commodity, market, model, date, forecast, lower, upper
    (optional: actual, segment = 'Backtest' | 'Forecast')."""
    if not FORECASTS_CSV_PATH.exists():
        return None
    f = pd.read_csv(FORECASTS_CSV_PATH, parse_dates=["date"])
    f = f[(f["commodity"] == commodity) & (f["market"] == market) & (f["model"] == model)]
    if f.empty:
        return None
    for col, default in (("lower", np.nan), ("upper", np.nan), ("actual", np.nan),
                         ("segment", "Forecast")):
        if col not in f.columns:
            f[col] = default
    f = f.sort_values("date")
    back = f[f["segment"] == "Backtest"]
    fut = f[f["segment"] == "Forecast"].head(horizon)
    return pd.concat([back, fut], ignore_index=True)[
        ["date", "forecast", "lower", "upper", "actual", "segment"]]


def get_forecast(series, commodity, market, model, horizon) -> pd.DataFrame:
    """Forecast retrieval for the dashboard (real file first, else DEMO)."""
    pre = _precomputed_forecast(commodity, market, model, horizon)
    if pre is not None:
        return pre
    fn = forecast_seasonal_naive if model == "Seasonal Naive" else forecast_sarima
    return fn(series, horizon, commodity, market)


# --------------------------------------------------------------------------- #
# Forecast evaluation  (TODO(REAL ANALYSIS): connect evaluation results)
# --------------------------------------------------------------------------- #
def get_model_metrics(df: pd.DataFrame, commodity: str, market: str) -> pd.DataFrame:
    """MAE/RMSE/MAPE per period and model -> [period, model, mae, rmse, mape, n_obs].

    Real file: data/model_metrics.csv with columns
    commodity, market, period, model, mae, rmse, mape, n_obs."""
    if METRICS_CSV_PATH.exists():
        m = pd.read_csv(METRICS_CSV_PATH)
        m = m[(m["commodity"] == commodity) & (m["market"] == market)]
        return m[["period", "model", "mae", "rmse", "mape", "n_obs"]].reset_index(drop=True)
    level = df.loc[(df["commodity"] == commodity) & (df["market"] == market), "price_php"].mean()
    return mock_data.mock_model_metrics(commodity, market, float(level) if pd.notna(level) else 50.0)
