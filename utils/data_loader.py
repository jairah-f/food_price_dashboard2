"""Centralised data loading.

The dashboard calls `load_food_price_data()` and nothing else to get prices.
If the WFP CSV is in /data it is used; otherwise DEMO data is generated.

Standard schema returned in both cases:
    date | commodity | category | region | province | market | unit | price_php
"""
import pandas as pd

from .config import FORECASTS_CSV_PATH, METRICS_CSV_PATH, WFP_CSV_PATH
from .mock_data import generate_mock_prices

try:  # Streamlit caching is optional so this module also works in plain scripts/tests
    import streamlit as st
    _cache = st.cache_data(show_spinner=False)
except Exception:  # pragma: no cover
    def _cache(fn):
        return fn

STANDARD_COLUMNS = ["date", "commodity", "category", "region", "province",
                    "market", "unit", "price_php"]


def using_demo_data() -> bool:
    return not WFP_CSV_PATH.exists()


def forecasts_are_demo() -> bool:
    return not FORECASTS_CSV_PATH.exists()


def metrics_are_demo() -> bool:
    return not METRICS_CSV_PATH.exists()


def _read_wfp_csv(path) -> pd.DataFrame:
    """Read the raw WFP file and return retail, nominal-PHP rows in the standard schema.

    TODO(REAL DATA): confirm column names against the final file. The HDX export
    uses: date, admin1, admin2, market, category, commodity, unit, pricetype,
    currency, price, usdprice. admin1 -> region, admin2 -> province is assumed.
    """
    raw = pd.read_csv(path, low_memory=False)
    # HDX files carry a second row of HXL tags (#date, #adm1+name, ...). Drop it.
    if len(raw) and raw.iloc[0].astype(str).str.startswith("#").any():
        raw = raw.iloc[1:].copy()

    # Retail only. Wholesale rows stay in the file but are excluded from analysis.
    if "pricetype" in raw.columns:
        raw = raw[raw["pricetype"].astype(str).str.lower().eq("retail")]

    df = raw.rename(columns={"admin1": "region", "admin2": "province", "price": "price_php"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    df["price_php"] = pd.to_numeric(df["price_php"], errors="coerce")  # nominal PHP; usdprice ignored
    df = df.dropna(subset=["date", "price_php"])
    # TODO(REAL DATA): harmonise region names to the study's 17 regions if needed.
    return df[STANDARD_COLUMNS].reset_index(drop=True)


@_cache
def _load_real(path_str: str, mtime: float) -> pd.DataFrame:
    return _read_wfp_csv(path_str)


@_cache
def _load_demo() -> pd.DataFrame:
    return generate_mock_prices()


def load_food_price_data() -> pd.DataFrame:
    """Single entry point for price data (real if available, else DEMO)."""
    if not using_demo_data():
        return _load_real(str(WFP_CSV_PATH), WFP_CSV_PATH.stat().st_mtime)
    return _load_demo()
