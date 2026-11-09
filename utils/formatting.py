"""Formatting helpers and UI building blocks (header, cards, KPI cards, empty states)."""
import html
from contextlib import contextmanager

import pandas as pd
import streamlit as st

from .config import ASSETS_DIR
from .data_loader import load_food_price_data, using_demo_data

PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}

METRIC_HELP = {
    "MAE": "Average size of the forecast error, in pesos.",
    "RMSE": "Like MAE, but large misses count more.",
    "MAPE": "Average error as a % of the actual price.",
}

# Simple outline icons (24x24, stroke only).
ICONS = {
    "records": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "basket": '<path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
    "pin": '<path d="M12 21s7-6.2 7-11a7 7 0 0 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "peso": '<path d="M7 20V4h6a4 4 0 0 1 0 8H7"/><path d="M5 8h11"/><path d="M5 11h11"/>',
    "trend": '<polyline points="3 17 9 11 13 15 21 7"/><polyline points="15 7 21 7 21 13"/>',
    "down": '<polyline points="3 7 9 13 13 9 21 17"/><polyline points="15 17 21 17 21 11"/>',
    "calendar": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>',
    "activity": '<polyline points="3 12 7 12 10 5 14 19 17 12 21 12"/>',
    "layers": '<polygon points="12 3 21 8 12 13 3 8 12 3"/><polyline points="3 13 12 18 21 13"/>',
}


def _ver() -> tuple:
    try:
        return tuple(int(x) for x in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)


# `width="stretch"` replaced `use_container_width=True` in recent Streamlit releases.
STRETCH = {"width": "stretch"} if _ver() >= (1, 50) else {"use_container_width": True}


def peso(x, decimals=2) -> str:
    return "—" if x is None or pd.isna(x) else f"₱{x:,.{decimals}f}"


def pct(x, decimals=1, signed=True) -> str:
    if x is None or pd.isna(x):
        return "—"
    return f"{x:+.{decimals}f}%" if signed else f"{x:.{decimals}f}%"


def month_label(ts) -> str:
    return "—" if ts is None or pd.isna(ts) else pd.Timestamp(ts).strftime("%b %Y")


def load_css() -> None:
    css = (ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def get_data() -> pd.DataFrame:
    """Price data with a loading indicator (cached after the first load)."""
    with st.spinner("Loading data…"):
        return load_food_price_data()


def page_header(title: str, subtitle: str = "", demo=None, pills=None) -> None:
    """Page title, optional subtitle and right-hand pills (e.g. date coverage)."""
    load_css()
    st.session_state["_card_i"] = 0
    demo = using_demo_data() if demo is None else demo
    chips = "".join(f'<span class="pill">{html.escape(p)}</span>' for p in (pills or []))
    chips += '<span class="demo-badge">DEMO DATA</span>' if demo else ""
    sub = f'<div class="page-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="page-head"><div><div class="page-title">{html.escape(title)}</div>'
                f'{sub}</div><div class="pills">{chips}</div></div>', unsafe_allow_html=True)


def section_title(text: str, demo=None, subtitle: str = "") -> None:
    demo = using_demo_data() if demo is None else demo
    pill = '<span class="demo-pill">DEMO</span>' if demo else ""
    sub = f'<div class="card-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="card-title">{html.escape(text)}{pill}</div>{sub}', unsafe_allow_html=True)


@contextmanager
def card(title=None, subtitle="", demo=None):
    """White rounded card. Usage: `with fmt.card("Title"): ...`"""
    n = st.session_state.get("_card_i", 0)
    st.session_state["_card_i"] = n + 1
    with st.container(key=f"card-{n}"):
        if title:
            section_title(title, demo=demo, subtitle=subtitle)
        yield


def kpi_cards(items, green_from=None) -> None:
    """items: (label, value, sub[, tone[, icon]]). tone is 'up'/'down' (colours the sub-text)."""
    cols = st.columns(len(items))
    for i, (col, item) in enumerate(zip(cols, items)):
        label, value, sub = item[:3]
        tone = item[3] if len(item) > 3 else ""
        icon = item[4] if len(item) > 4 else "layers"
        sub_html = f'<div class="kpi-sub {tone}">{html.escape(str(sub))}</div>' if sub else ""
        col.markdown(
            f'<div class="kpi accent-{i % 4}"><div class="kpi-icon"><svg viewBox="0 0 24 24">'
            f'{ICONS.get(icon, ICONS["layers"])}</svg></div><div><div class="kpi-label">{html.escape(label)}</div>'
            f'<div class="kpi-value">{html.escape(str(value))}</div>{sub_html}</div></div>',
            unsafe_allow_html=True)


def legend_row(items) -> None:
    """items: [(colour, label)] shown as a small key under a chart title."""
    st.markdown('<div class="legend-row">' + "".join(
        f'<span><span class="dot" style="background:{c}"></span>{html.escape(t)}</span>'
        for c, t in items) + "</div>", unsafe_allow_html=True)


def empty_state(title: str, text: str = "") -> None:
    st.markdown(f'<div class="empty"><b>{html.escape(title)}</b>{html.escape(text)}</div>',
                unsafe_allow_html=True)


def show_chart(fig, key=None) -> None:
    st.plotly_chart(fig, config=PLOT_CONFIG, key=key, **STRETCH)


def trend_tone(value) -> str:
    if value is None or pd.isna(value) or value == 0:
        return ""
    return "up" if value > 0 else "down"
