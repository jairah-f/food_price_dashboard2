"""Display-level aggregations used only by the redesigned UI.

These are descriptive summaries of whatever data is loaded (real or demo).
They are NOT research results and do not replace anything in analysis.py.
"""
import numpy as np
import pandas as pd

from .analysis import assign_period
from .config import PERIOD_ORDER


def coverage(df: pd.DataFrame) -> dict:
    """Dataset coverage computed from the loaded data (nothing hardcoded)."""
    if df.empty:
        return {"records": 0, "commodities": 0, "regions": 0, "markets": 0,
                "start": None, "end": None, "avg_price": np.nan, "avg_note": ""}
    kg = df[df["unit"].astype(str).str.upper().eq("KG")]
    base, note = (kg, "per kg · eggs excluded") if len(kg) else (df, "all units")
    return {"records": len(df), "commodities": df["commodity"].nunique(),
            "regions": df["region"].nunique(), "markets": df["market"].nunique(),
            "start": df["date"].min(), "end": df["date"].max(),
            "avg_price": float(base["price_php"].mean()), "avg_note": note}


def with_period(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(period=assign_period(df["date"])).dropna(subset=["period"])


def commodity_insights(df: pd.DataFrame) -> pd.DataFrame:
    """Latest 12 months vs. the 12 months before -> % change per commodity."""
    if df.empty:
        return pd.DataFrame()
    last = df["date"].max()
    cut = last - pd.DateOffset(months=11)
    prior_from = last - pd.DateOffset(months=23)
    cur = df[df["date"] >= cut].groupby("commodity")["price_php"].mean().rename("latest_avg")
    prev = df[(df["date"] >= prior_from) & (df["date"] < cut)].groupby("commodity")["price_php"].mean().rename("prior_avg")
    out = pd.concat([cur, prev], axis=1).dropna().reset_index()
    out["change_pct"] = (out["latest_avg"] / out["prior_avg"] - 1) * 100
    unit = df.groupby("commodity")["unit"].agg(lambda s: s.mode().iat[0])
    out["unit"] = out["commodity"].map(unit)
    return out.reindex(out["change_pct"].abs().sort_values(ascending=False).index).reset_index(drop=True)


def commodity_period_table(df: pd.DataFrame, periods=None) -> pd.DataFrame:
    """Average price per commodity and period, plus % change between periods."""
    periods = periods or PERIOD_ORDER
    d = with_period(df)
    if d.empty:
        return pd.DataFrame()
    g = d.groupby(["commodity", "period"])["price_php"].mean().unstack().reindex(columns=PERIOD_ORDER)
    g["pre_to_pandemic"] = (g["Pandemic"] / g["Pre-Pandemic"] - 1) * 100
    g["pandemic_to_post"] = (g["Post-Pandemic"] / g["Pandemic"] - 1) * 100
    return g.reset_index()


def moving_average(series: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling mean of a [date, price] series (display smoothing only)."""
    s = series.sort_values("date").copy()
    s["price"] = s["price"].rolling(window, min_periods=max(2, window // 2)).mean()
    return s.dropna(subset=["price"])


def best_model_by_period(perf: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Which model has the lower error in each period -> [period, model, other, gap_pct]."""
    rows = []
    for p in PERIOD_ORDER:
        g = perf[perf["period"] == p].sort_values(metric)
        if len(g) >= 2 and g[metric].iloc[1] > 0:
            rows.append({"period": p, "model": g["model"].iloc[0], "other": g["model"].iloc[1],
                         "gap_pct": (1 - g[metric].iloc[0] / g[metric].iloc[1]) * 100})
    return pd.DataFrame(rows, columns=["period", "model", "other", "gap_pct"])
