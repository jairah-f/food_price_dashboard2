"""Forecasting - historical vs. forecasted prices (uses analysis.get_forecast)."""
import streamlit as st

from utils import analysis, filters, formatting as fmt, visualizations as viz
from utils.config import HORIZONS, MODELS
from utils.data_loader import forecasts_are_demo, using_demo_data
from utils.theme import MUTED, NAVY, TEAL

demo = using_demo_data() or forecasts_are_demo()
fmt.page_header("Forecasting", "Historical retail prices alongside model forecasts", demo=demo)
df = fmt.get_data()
if df.empty:
    fmt.empty_state("No data loaded", "Add the WFP CSV to the data folder.")
    st.stop()

with fmt.card():
    cols = st.columns(5)
    sel = filters.location_filters(df, require_market=True, slots=cols)
    c1, c2 = st.columns([2, 2])
    model = filters.sticky_select("Model", MODELS, "sel_model", MODELS[0], kind="radio",
                                  container=c1, horizontal=True)
    horizon = c2.select_slider("Forecast horizon (months)", HORIZONS,
                               value=st.session_state.get("sel_horizon", 6))
    st.session_state["sel_horizon"] = horizon

if not sel["market"]:
    fmt.empty_state("No market available", "Choose another commodity or region.")
    st.stop()

series = analysis.monthly_series(
    filters.apply_filters(df, commodity=sel["commodity"], market=sel["market"]))
if not analysis.is_eligible_series(series):
    fmt.empty_state("Not enough observations to forecast this series",
                    "Pick a market with a longer price history.")
    st.stop()

with st.spinner("Preparing forecast…"):
    fc = analysis.get_forecast(series, sel["commodity"], sel["market"], model, horizon)
future = fc[fc["segment"] == "Forecast"]
if future.empty:
    fmt.empty_state("No forecast available for this selection")
    st.stop()

unit = df.loc[df["commodity"] == sel["commodity"], "unit"].mode().iat[0]
latest = float(series["price"].iloc[-1])
nxt = float(future["forecast"].iloc[0])
change = (nxt / latest - 1) * 100 if latest else float("nan")
direction = "Stable" if abs(change) < 0.5 else ("Rising" if change > 0 else "Falling")

st.write("")
fmt.kpi_cards([
    ("Latest observed price", fmt.peso(latest), f'{fmt.month_label(series["date"].iloc[-1])} · per {unit.lower()}',
     "", "peso"),
    ("Forecasted price", fmt.peso(nxt), f'{fmt.month_label(future["date"].iloc[0])} · {model}', "", "target"),
    ("Forecast direction", direction, f"{fmt.pct(change)} vs. latest observed", fmt.trend_tone(change),
     "down" if change < 0 else "trend"),
    ("Forecast period", f"{horizon} months",
     f'{fmt.month_label(future["date"].iloc[0])} – {fmt.month_label(future["date"].iloc[-1])}', "", "calendar"),
])
st.write("")

with fmt.card(f'{sel["commodity"]} · {sel["market"]}', "Historical vs. forecasted prices", demo=demo):
    legend = [(NAVY, "Historical (actual)"), (MUTED, "Predicted, past months (backtest)"),
              (TEAL, f"Forecast ({model})")]
    fmt.legend_row(legend)
    fmt.show_chart(viz.forecast_fig(series, fc, model, unit), key="fc_main")

with st.expander("Forecast values"):
    table = future[["date", "forecast", "lower", "upper"]].copy()
    table["date"] = table["date"].dt.strftime("%b %Y")
    table.columns = ["Month", "Forecast", "Lower", "Upper"]
    st.dataframe(table.style.format({c: "₱{:,.2f}" for c in ["Forecast", "Lower", "Upper"]}, na_rep="—"),
                 hide_index=True, **fmt.STRETCH)
