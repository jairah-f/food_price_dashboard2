"""Plotly figure builders. Pure functions: DataFrame in, Figure out."""
import pandas as pd
import plotly.graph_objects as go

from .config import PERIOD_ORDER, PERIOD_RANGE_LABELS, PERIODS
from .theme import (CATEGORY_COLORS, CORAL, GRID, INK, MODEL_COLORS, MUTED, NAVY,
                    PERIOD_COLORS, SAGE, SLATE, TEAL)

FONT = "Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
TEAL_BAND = "rgba(111,175,165,0.22)"


def _style(fig, height=360, legend=True):
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=8, r=8, t=30, b=8),
        font=dict(family=FONT, size=13, color=INK), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
        legend=dict(orientation="h", y=1.12, x=0, title_text="", font=dict(size=12)),
        hoverlabel=dict(bgcolor="white", font_size=13, bordercolor=GRID), hovermode="closest",
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, title_text=None, tickfont=dict(size=12))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title_text=None, tickfont=dict(size=12))
    return fig


def _empty(message="No data for this selection", height=300):
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(color=MUTED, size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _style(fig, height=height, legend=False)


def _iso(ts) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m-%d")


# ---------------------------- Overview ------------------------------------ #
def category_trend_fig(cs, mode="Index", height=360):
    if cs.empty:
        return _empty(height=height)
    fig = go.Figure()
    for i, (cat, g) in enumerate(cs.groupby("category")):
        g = g.sort_values("date")
        fig.add_trace(go.Scatter(
            x=g["date"], y=g["value"], mode="lines", name=cat,
            line=dict(width=2.2, color=CATEGORY_COLORS[i % len(CATEGORY_COLORS)]),
            hovertemplate=("%{x|%b %Y}<br>" + cat + "<br>" +
                           ("Index %{y:.1f}" if mode == "Index" else "₱%{y:,.2f}") + "<extra></extra>")))
    fig.update_xaxes(title_text="Date")
    if mode == "Index":
        fig.update_yaxes(title_text="Index (start of range = 100)")
    else:
        fig.update_yaxes(tickprefix="₱", title_text="Average price (₱)")
    fig.update_layout(hovermode="x unified")
    return _style(fig, height=height)


def price_distribution_fig(d, height=340):
    """Box plot of prices by period. `d` needs columns [period, price_php]."""
    if d.empty:
        return _empty(height=height)
    fig = go.Figure()
    for p in PERIOD_ORDER:
        g = d[d["period"] == p]
        if g.empty:
            continue
        fig.add_trace(go.Box(
            y=g["price_php"], name=p, marker_color=PERIOD_COLORS[p], line=dict(color=PERIOD_COLORS[p]),
            fillcolor=PERIOD_COLORS[p], opacity=0.85, boxpoints="outliers", marker_size=3,
            hovertemplate="%{y:,.2f}<extra>" + p + "</extra>"))
    fig.update_yaxes(tickprefix="₱", title_text="Price (₱)")
    return _style(fig, height=height, legend=False)


def commodity_insights_fig(ins, top=8, height=340):
    """Largest price movements: latest 12 months vs. the 12 months before."""
    if ins.empty:
        return _empty("Not enough history to compare", height)
    t = ins.head(top).sort_values("change_pct")
    fig = go.Figure(go.Bar(
        x=t["change_pct"], y=t["commodity"], orientation="h",
        marker_color=[CORAL if v >= 0 else TEAL for v in t["change_pct"]],
        text=[f"{v:+.1f}%" for v in t["change_pct"]], textposition="outside", cliponaxis=False,
        customdata=t[["latest_avg", "prior_avg"]].to_numpy(),
        hovertemplate=("<b>%{y}</b><br>%{x:+.2f}%<br>Latest 12 mo: ₱%{customdata[0]:,.2f}"
                       "<br>Previous 12 mo: ₱%{customdata[1]:,.2f}<extra></extra>")))
    lim = max(abs(t["change_pct"]).max(), 1) * 1.35
    fig.update_xaxes(ticksuffix="%", range=[-lim, lim], showgrid=True, gridcolor=GRID, zeroline=True,
                     zerolinecolor=MUTED)
    return _style(fig, height=height, legend=False)


# ----------------------- Historical trends -------------------------------- #
def price_trend_fig(series, commodity, market_label, unit="KG", ma=None, ma_label="", height=400):
    if series.empty:
        return _empty(height=height)
    s = series.sort_values("date")
    avg = s["price"].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s["date"], y=s["price"], mode="lines+markers", name="Retail price",
        line=dict(color=NAVY, width=2.2), marker=dict(size=4),
        customdata=[[commodity, market_label, unit]] * len(s),
        hovertemplate=("<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{x|%b %Y}<br>"
                       "₱%{y:,.2f} / %{customdata[2]}<extra></extra>")))
    if ma is not None and len(ma):
        fig.add_trace(go.Scatter(
            x=ma["date"], y=ma["price"], mode="lines", name=ma_label,
            line=dict(color=CORAL, width=2.4),
            hovertemplate="%{x|%b %Y}<br>" + ma_label + " ₱%{y:,.2f}<extra></extra>"))
    lo, hi = s.loc[s["price"].idxmin()], s.loc[s["price"].idxmax()]
    fig.add_trace(go.Scatter(
        x=[lo["date"], hi["date"]], y=[lo["price"], hi["price"]], mode="markers", name="Min / Max",
        marker=dict(size=10, color=TEAL, line=dict(color="white", width=1.5)),
        hovertemplate="%{x|%b %Y}<br>₱%{y:,.2f}<extra></extra>"))
    fig.add_hline(y=avg, line_dash="dot", line_color=MUTED, annotation_text=f"Avg ₱{avg:,.2f}",
                  annotation_position="top left", annotation_font=dict(size=12, color=MUTED))
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(tickprefix="₱", title_text=f"Price (₱ per {unit.lower()})")
    return _style(fig, height=height)


# ------------------------ Period comparison -------------------------------- #
def period_avg_bar(summary, height=340):
    s = summary.dropna(subset=["avg_price"])
    if s.empty:
        return _empty(height=height)
    fig = go.Figure(go.Bar(
        x=s["period"], y=s["avg_price"], marker_color=[PERIOD_COLORS[p] for p in s["period"]],
        text=[f"₱{v:,.2f}" for v in s["avg_price"]], textposition="outside", cliponaxis=False,
        customdata=s["n_obs"],
        hovertemplate="%{x}<br>₱%{y:,.2f}<br>%{customdata:,} observations<extra></extra>"))
    fig.update_yaxes(tickprefix="₱", title_text="Average price (₱)", range=[0, s["avg_price"].max() * 1.2])
    return _style(fig, height=height, legend=False)


def period_change_bar(changes, height=340):
    if changes.empty:
        return _empty("Not enough periods with data", height)
    fig = go.Figure(go.Bar(
        x=changes["comparison"], y=changes["pct_change"],
        marker_color=[CORAL if v >= 0 else TEAL for v in changes["pct_change"]],
        text=[f"{v:+.1f}%" for v in changes["pct_change"]], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}<br>%{y:+.2f}%<extra></extra>"))
    fig.update_yaxes(ticksuffix="%", title_text="Change in average price")
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    return _style(fig, height=height, legend=False)


def trend_shading_fig(series, periods=None, height=340):
    if series.empty:
        return _empty(height=height)
    periods = periods or PERIOD_ORDER
    s = series.sort_values("date")
    fig = go.Figure(go.Scatter(
        x=s["date"], y=s["price"], mode="lines", name="Retail price", line=dict(color=NAVY, width=2.2),
        hovertemplate="%{x|%b %Y}<br>₱%{y:,.2f}<extra></extra>"))
    lo, hi = s["date"].min(), s["date"].max()
    for p in periods:
        start, end = PERIODS[p]
        start, end = max(start, lo), min(end, hi)
        if start >= end:
            continue
        fig.add_shape(type="rect", xref="x", yref="paper", x0=_iso(start), x1=_iso(end), y0=0, y1=1,
                      fillcolor=PERIOD_COLORS[p], opacity=0.28, line_width=0, layer="below")
        fig.add_annotation(x=_iso(start + (end - start) / 2), y=1.0, yref="paper", yanchor="bottom",
                           text=p, showarrow=False, font=dict(size=12, color=INK))
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(tickprefix="₱", title_text="Price (₱)")
    return _style(fig, height=height, legend=False)


def regional_comparison_fig(rp):
    if rp.empty:
        return _empty()
    regions = sorted(rp["region"].unique(), reverse=True)
    fig = go.Figure()
    for p in PERIOD_ORDER:
        g = rp[rp["period"] == p]
        if g.empty:
            continue
        fig.add_trace(go.Bar(
            y=g["region"], x=g["avg_price"], name=p, orientation="h", marker_color=PERIOD_COLORS[p],
            hovertemplate="%{y}<br>" + p + "<br>₱%{x:,.2f}<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(categoryorder="array", categoryarray=regions)
    fig.update_xaxes(tickprefix="₱", showgrid=True, gridcolor=GRID, title_text="Average price (₱)")
    return _style(fig, height=max(420, 20 * len(regions) * 3))


def commodity_change_fig(table, height=420):
    """% change into the Pandemic and Post-Pandemic periods, per commodity."""
    if table.empty:
        return _empty(height=height)
    t = table.sort_values("pre_to_pandemic", na_position="first")
    fig = go.Figure()
    for col, name, color in (("pre_to_pandemic", "Pre-Pandemic → Pandemic", PERIOD_COLORS["Pandemic"]),
                             ("pandemic_to_post", "Pandemic → Post-Pandemic", PERIOD_COLORS["Post-Pandemic"])):
        fig.add_trace(go.Bar(y=t["commodity"], x=t[col], name=name, orientation="h", marker_color=color,
                             hovertemplate="%{y}<br>" + name + ": %{x:+.2f}%<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor=MUTED,
                     title_text="Change in average price")
    return _style(fig, height=height)


# ----------------------------- Forecasting --------------------------------- #
def forecast_fig(hist, fc, model, unit="KG", height=440):
    if hist.empty:
        return _empty(height=height)
    hist = hist.sort_values("date")
    last_date = hist["date"].iloc[-1]
    last_val = float(hist["price"].iloc[-1])
    back = fc[fc["segment"] == "Backtest"] if len(fc) else fc
    fut = fc[fc["segment"] == "Forecast"] if len(fc) else fc

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist["date"], y=hist["price"], mode="lines", name="Historical (actual)",
        line=dict(color=NAVY, width=2.4),
        hovertemplate=f"%{{x|%b %Y}}<br>Actual ₱%{{y:,.2f}} / {unit.lower()}<extra></extra>"))
    if len(back):
        fig.add_trace(go.Scatter(
            x=back["date"], y=back["forecast"], mode="lines+markers", name="Predicted (backtest)",
            line=dict(color=MUTED, width=1.6, dash="dot"), marker=dict(size=6),
            hovertemplate="%{x|%b %Y}<br>Predicted ₱%{y:,.2f}<extra></extra>"))
    if len(fut):
        xs = [last_date] + fut["date"].tolist()
        ys = [last_val] + fut["forecast"].tolist()
        if fut["lower"].notna().all() and fut["upper"].notna().all():
            up = [last_val] + fut["upper"].tolist()
            lw = [last_val] + fut["lower"].tolist()
            fig.add_trace(go.Scatter(
                x=xs + xs[::-1], y=up + lw[::-1], fill="toself", mode="lines",
                fillcolor=TEAL_BAND, line=dict(width=0), name="Confidence interval", hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers", name=f"Forecast ({model})",
            line=dict(color=TEAL, width=3, dash="dash"), marker=dict(size=7),
            hovertemplate="%{x|%b %Y}<br>Forecast ₱%{y:,.2f}<extra></extra>"))
        fig.add_shape(type="rect", xref="x", yref="paper", x0=_iso(last_date),
                      x1=_iso(fut["date"].iloc[-1]), y0=0, y1=1,
                      fillcolor=TEAL, opacity=0.07, line_width=0, layer="below")
    fig.add_shape(type="line", xref="x", yref="paper", x0=_iso(last_date), x1=_iso(last_date),
                  y0=0, y1=1, line=dict(color=MUTED, width=1, dash="dot"))
    fig.add_annotation(x=_iso(last_date), y=1.0, yref="paper", yanchor="bottom", text="Forecast start",
                       showarrow=False, font=dict(size=12, color=MUTED))
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(tickprefix="₱", title_text=f"Price (₱ per {unit.lower()})")
    return _style(fig, height=height)


# ------------------------- Model evaluation -------------------------------- #
_METRIC_FMT = {"mae": ("MAE", "₱{:,.2f}", "₱"), "rmse": ("RMSE", "₱{:,.2f}", "₱"),
               "mape": ("MAPE", "{:.2f}%", "")}


def actual_vs_predicted_fig(actual, preds, height=340):
    """actual: [date, price]; preds: {model: [date, forecast]} for the evaluation window."""
    if actual.empty or not preds:
        return _empty("No actual-vs-predicted values available", height)
    fig = go.Figure(go.Scatter(
        x=actual["date"], y=actual["price"], mode="lines+markers", name="Actual",
        line=dict(color=NAVY, width=2.4), marker=dict(size=6),
        hovertemplate="%{x|%b %Y}<br>Actual ₱%{y:,.2f}<extra></extra>"))
    for model, p in preds.items():
        fig.add_trace(go.Scatter(
            x=p["date"], y=p["forecast"], mode="lines+markers", name=f"{model} (predicted)",
            line=dict(color=MODEL_COLORS.get(model, TEAL), width=2.2, dash="dash"), marker=dict(size=7),
            hovertemplate="%{x|%b %Y}<br>" + model + " ₱%{y:,.2f}<extra></extra>"))
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(tickprefix="₱", title_text="Price (₱)")
    return _style(fig, height=height)


def metric_compare_bar(perf_period, metric, height=270):
    """Seasonal Naive vs SARIMA for one metric and one period."""
    if perf_period.empty:
        return _empty(height=height)
    name, fmt, prefix = _METRIC_FMT[metric]
    fig = go.Figure(go.Bar(
        x=perf_period["model"], y=perf_period[metric],
        marker_color=[MODEL_COLORS.get(m, NAVY) for m in perf_period["model"]],
        text=[fmt.format(v) for v in perf_period[metric]], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}<br>" + name + " " + fmt.replace("{:", "%{y:") + "<extra></extra>"))
    fig.update_yaxes(tickprefix=prefix, ticksuffix="%" if metric == "mape" else "",
                     range=[0, perf_period[metric].max() * 1.28])
    return _style(fig, height=height, legend=False)


def accuracy_across_periods_fig(perf, metric, height=340):
    if perf.empty:
        return _empty(height=height)
    name, fmt, prefix = _METRIC_FMT[metric]
    fig = go.Figure()
    for model, g in perf.groupby("model"):
        g = g.set_index("period").reindex([p for p in PERIOD_ORDER if p in set(g["period"])]).reset_index()
        fig.add_trace(go.Bar(
            x=g["period"], y=g[metric], name=model, marker_color=MODEL_COLORS.get(model, NAVY),
            text=[fmt.format(v) for v in g[metric]], textposition="outside", cliponaxis=False,
            hovertemplate="%{x}<br>" + model + "<br>" + name + ": %{y:,.2f}<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(tickprefix=prefix, ticksuffix="%" if metric == "mape" else "", title_text=name)
    return _style(fig, height=height)
