"""DEMO DATA GENERATORS - everything here is synthetic.

These functions only exist so the dashboard runs before the real analysis is
finished. Nothing produced here is a research finding. When real data/outputs
are available, `data_loader.py` and `analysis.py` stop calling this module.
"""
import zlib

import numpy as np
import pandas as pd

from .config import MODELS

# (commodity, category, unit, base price 2016, annual drift, seasonal amplitude, phase)
_COMMODITIES = [
    ("Rice (Regular Milled)", "Cereals and tubers", "KG", 38.0, 0.020, 0.010, 0.4),
    ("Rice (Well Milled)", "Cereals and tubers", "KG", 43.0, 0.020, 0.010, 0.5),
    ("Sweet potatoes", "Cereals and tubers", "KG", 30.0, 0.030, 0.050, 1.2),
    ("Pork (with bones)", "Meat, fish and eggs", "KG", 180.0, 0.040, 0.020, 2.0),
    ("Chicken (Whole)", "Meat, fish and eggs", "KG", 135.0, 0.025, 0.025, 2.4),
    ("Fish (Tilapia)", "Meat, fish and eggs", "KG", 100.0, 0.035, 0.030, 0.9),
    ("Eggs (Chicken)", "Meat, fish and eggs", "UNIT", 5.5, 0.030, 0.030, 3.0),
    ("Tomatoes", "Vegetables and fruits", "KG", 40.0, 0.030, 0.150, 1.7),
    ("Onions (Red)", "Vegetables and fruits", "KG", 70.0, 0.035, 0.120, 2.6),
    ("Bananas (Lakatan)", "Vegetables and fruits", "KG", 50.0, 0.030, 0.040, 0.2),
    ("Sugar (Brown)", "Miscellaneous food", "KG", 45.0, 0.030, 0.015, 1.0),
    ("Salt (Iodized)", "Miscellaneous food", "KG", 22.0, 0.020, 0.005, 0.0),
]

# (region, province, market) - 17 regions, 2 demo markets each
_LOCATIONS = [
    ("NCR", "Metro Manila", "Manila"), ("NCR", "Metro Manila", "Quezon City"),
    ("CAR", "Benguet", "Baguio City"), ("CAR", "Kalinga", "Tabuk"),
    ("Region I", "Ilocos Norte", "Laoag"), ("Region I", "Pangasinan", "Dagupan"),
    ("Region II", "Isabela", "Ilagan"), ("Region II", "Cagayan", "Tuguegarao"),
    ("Region III", "Pampanga", "San Fernando"), ("Region III", "Bulacan", "Malolos"),
    ("Region IV-A", "Laguna", "Calamba"), ("Region IV-A", "Batangas", "Batangas City"),
    ("MIMAROPA", "Palawan", "Puerto Princesa"), ("MIMAROPA", "Oriental Mindoro", "Calapan"),
    ("Region V", "Albay", "Legazpi"), ("Region V", "Camarines Sur", "Naga"),
    ("Region VI", "Iloilo", "Iloilo City"), ("Region VI", "Negros Occidental", "Bacolod"),
    ("Region VII", "Cebu", "Cebu City"), ("Region VII", "Bohol", "Tagbilaran"),
    ("Region VIII", "Leyte", "Tacloban"), ("Region VIII", "Samar", "Catbalogan"),
    ("Region IX", "Zamboanga del Sur", "Zamboanga City"), ("Region IX", "Zamboanga del Norte", "Dipolog"),
    ("Region X", "Misamis Oriental", "Cagayan de Oro"), ("Region X", "Bukidnon", "Malaybalay"),
    ("Region XI", "Davao del Sur", "Davao City"), ("Region XI", "Davao de Oro", "Nabunturan"),
    ("Region XII", "South Cotabato", "General Santos"), ("Region XII", "Cotabato", "Kidapawan"),
    ("Region XIII", "Agusan del Norte", "Butuan"), ("Region XIII", "Surigao del Norte", "Surigao City"),
    ("BARMM", "Maguindanao", "Cotabato City"), ("BARMM", "Lanao del Sur", "Marawi"),
]


def _rng(*parts) -> np.random.Generator:
    """Deterministic RNG so demo values stay stable between reruns."""
    return np.random.default_rng(zlib.crc32("|".join(map(str, parts)).encode()))


def generate_mock_prices() -> pd.DataFrame:
    """DEMO monthly retail price panel in the same schema as the real loader."""
    dates = pd.date_range("2016-01-01", "2026-06-01", freq="MS")
    t = np.arange(len(dates)) / 12.0
    region_factor = {r: _rng("region", r).uniform(0.94, 1.10) for r, _, _ in _LOCATIONS}
    frames = []
    for name, cat, unit, base, drift, amp, phase in _COMMODITIES:
        shock_amp = _rng("shock", name).uniform(0.03, 0.12)
        shock = shock_amp * np.exp(-((t - 6.3) / 1.1) ** 2)
        for region, province, market in _LOCATIONS:
            rng = _rng("series", name, market)
            # a few demo series are missing entirely, to exercise the "no data" handling
            if name != "Rice (Regular Milled)" and rng.random() < 0.10:
                continue
            walk = np.cumsum(rng.normal(0, 0.008, len(dates)))
            walk -= np.linspace(0, walk[-1], len(dates))  # keep the walk from drifting away
            price = (
                base * region_factor[region] * (1 + drift) ** t
                * (1 + amp * np.sin(2 * np.pi * t + phase))
                * (1 + shock) * np.exp(walk + rng.normal(0, 0.012, len(dates)))
            )
            keep = rng.random(len(dates)) > 0.02  # scattered missing months
            if name != "Rice (Regular Milled)" and rng.random() < 0.12:
                # drop one whole period window for some series
                lo, hi = [(0, 50), (50, 83), (83, len(dates))][int(rng.integers(0, 3))]
                keep[lo:hi] = False
            frames.append(pd.DataFrame({
                "date": dates[keep], "commodity": name, "category": cat,
                "region": region, "province": province, "market": market,
                "unit": unit, "price_php": np.round(price[keep], 2),
            }))
    return pd.concat(frames, ignore_index=True)


def mock_forecast(series: pd.DataFrame, model: str, horizon: int, key: str) -> pd.DataFrame:
    """DEMO forecast. NOT produced by Seasonal Naive or SARIMA.

    `series` has columns [date, price]. Returns columns
    [date, forecast, lower, upper, actual, segment] where segment is
    'Backtest' (predicted vs. actual) or 'Forecast' (future).
    """
    s = series.sort_values("date")
    hist = s["price"].to_numpy(dtype=float)
    last_date = s["date"].iloc[-1]
    rng = _rng("forecast", model, key)
    level = float(np.mean(hist[-3:]))
    fdates = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    h = np.arange(1, horizon + 1)
    seas = 0.025 * np.sin(2 * np.pi * fdates.month.to_numpy() / 12 + 1.0)
    if model == "SARIMA":
        path = level * (1 + rng.uniform(-0.002, 0.006) * h) * (1 + seas)
        sd = 0.018 * np.sqrt(h)
        bt_noise = 0.020
    else:
        path = level * (1 + 1.3 * seas)
        sd = 0.030 + 0.004 * h
        bt_noise = 0.030
    path = path + rng.normal(0, 0.004 * level, horizon)
    future = pd.DataFrame({
        "date": fdates, "forecast": np.round(path, 2),
        "lower": np.round(path * (1 - 1.96 * sd), 2),
        "upper": np.round(path * (1 + 1.96 * sd), 2),
        "actual": np.nan, "segment": "Forecast",
    })
    n_bt = min(6, max(len(hist) - 12, 0))
    if n_bt:
        actual = hist[-n_bt:]
        back = pd.DataFrame({
            "date": s["date"].iloc[-n_bt:].to_numpy(),
            "forecast": np.round(actual * (1 + rng.normal(0, bt_noise, n_bt)), 2),
            "lower": np.nan, "upper": np.nan, "actual": actual, "segment": "Backtest",
        })
        return pd.concat([back, future], ignore_index=True)
    return future


def mock_model_metrics(commodity: str, market: str, price_level: float) -> pd.DataFrame:
    """DEMO MAE/RMSE/MAPE per period and model. Values are random on purpose:
    neither model is favoured."""
    rng = _rng("metrics", commodity, market)
    n_range = {"Pre-Pandemic": (38, 50), "Pandemic": (24, 34), "Post-Pandemic": (28, 40)}
    rows = []
    for period, (lo, hi) in n_range.items():
        n_obs = int(rng.integers(lo, hi))
        base = rng.uniform(2.0, 7.0) * rng.uniform(0.8, 1.8)
        for model in MODELS:
            mape = base * rng.uniform(0.75, 1.25)
            mae = mape / 100 * price_level * rng.uniform(0.85, 1.0)
            rows.append({"period": period, "model": model, "mae": mae,
                         "rmse": mae * rng.uniform(1.15, 1.40), "mape": mape, "n_obs": n_obs})
    return pd.DataFrame(rows)
