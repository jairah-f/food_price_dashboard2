"""Filtering logic and filter widgets.

`apply_filters` is pure pandas (unchanged). Widgets keep selections in session
state so commodity / region / market stay connected across pages.

Redesign: widgets can now be placed into page-level columns via `slots`
(a list of Streamlit containers, one per visible filter). With no slots they
fall back to the sidebar, exactly as before.
"""
import pandas as pd
import streamlit as st

from .config import DEFAULT_COMMODITY

ALL = "All"


def apply_filters(df: pd.DataFrame, category=None, commodity=None, region=None,
                  province=None, market=None, start=None, end=None) -> pd.DataFrame:
    """Filter by any combination of fields. None means no filter."""
    out = df
    for col, val in (("category", category), ("commodity", commodity), ("region", region),
                     ("province", province), ("market", market)):
        if val is not None:
            out = out[out[col] == val]
    if start is not None:
        out = out[out["date"] >= pd.Timestamp(start)]
    if end is not None:
        out = out[out["date"] <= pd.Timestamp(end)]
    return out


def _options(df: pd.DataFrame, col: str) -> list:
    return sorted(df[col].dropna().unique().tolist())


def sticky_select(label, options, state_key, default=None, kind="select", container=None,
                  horizontal=False):
    """Selectbox/radio whose value survives page changes via session state."""
    c = container or st.sidebar
    if not options:
        c.selectbox(label, ["No data"], disabled=True)
        return None
    cur = st.session_state.get(state_key, default)
    idx = options.index(cur) if cur in options else 0
    if kind == "radio":
        value = c.radio(label, options, index=idx, horizontal=horizontal)
    else:
        value = c.selectbox(label, options, index=idx)
    st.session_state[state_key] = value
    return value


def location_filters(df, *, require_market=False, show_category=True, show_province=True,
                     show_market=True, slots=None) -> dict:
    """Cascading Category > Commodity > Region > Province > Market filters.

    Returns {category, commodity, region, province, market}; 'All' becomes None.
    `slots`: containers for the visible filters, in that order (commodity and region
    are always visible).
    """
    out = dict(category=None, commodity=None, region=None, province=None, market=None)
    it = iter(slots) if slots else None
    nxt = (lambda: next(it)) if it else (lambda: None)
    d = df
    if show_category:
        cat = sticky_select("Food category", [ALL] + _options(d, "category"), "sel_category", ALL,
                            container=nxt())
        if cat not in (None, ALL):
            out["category"], d = cat, d[d["category"] == cat]
    commodity = sticky_select("Commodity", _options(d, "commodity"), "sel_commodity",
                              DEFAULT_COMMODITY, container=nxt())
    out["commodity"] = commodity
    d = d[d["commodity"] == commodity] if commodity else d.iloc[0:0]

    region = sticky_select("Region", [ALL] + _options(d, "region"), "sel_region", ALL, container=nxt())
    if region not in (None, ALL):
        out["region"], d = region, d[d["region"] == region]
    if show_province:
        prov = sticky_select("Province", [ALL] + _options(d, "province"), "sel_province", ALL,
                             container=nxt())
        if prov not in (None, ALL):
            out["province"], d = prov, d[d["province"] == prov]
    if show_market:
        markets = _options(d, "market")
        market = sticky_select("Market", markets if require_market else [ALL] + markets,
                               "sel_market", None if require_market else ALL, container=nxt())
        if market not in (None, ALL):
            out["market"] = market
    return out


def date_range_filter(df: pd.DataFrame, container=None):
    """Month slider -> (start, end) as Timestamps."""
    c = container or st.sidebar
    lo, hi = df["date"].min().to_pydatetime(), df["date"].max().to_pydatetime()
    if lo >= hi:
        return pd.Timestamp(lo), pd.Timestamp(hi)
    value = st.session_state.get("sel_dates", (lo, hi))
    value = (max(value[0], lo), min(value[1], hi))
    start, end = c.slider("Date range", min_value=lo, max_value=hi, value=value, format="MMM YYYY")
    st.session_state["sel_dates"] = (start, end)
    return pd.Timestamp(start), pd.Timestamp(end)
