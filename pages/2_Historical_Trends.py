"""Price Trends - explore historical retail prices."""
import streamlit as st

from utils import analysis, filters, formatting as fmt, ui_analytics as ui, visualizations as viz

fmt.page_header("Price Trends", "Explore historical retail prices by commodity and location")
df = fmt.get_data()
if df.empty:
    fmt.empty_state("No data loaded", "Add the WFP CSV to the data folder.")
    st.stop()

with fmt.card():
    cols = st.columns(5)
    sel = filters.location_filters(df, slots=cols)
    c1, c2 = st.columns([3, 1])
    start, end = filters.date_range_filter(df, container=c1)
    ma_choice = c2.selectbox("Moving average", ["Off", "3-month", "6-month", "12-month"])

filtered = filters.apply_filters(df, **sel, start=start, end=end)
series = analysis.monthly_series(filtered)
if len(series) < 2:
    fmt.empty_state("No observations for this selection", "Try another market or a wider date range.")
    st.stop()

summary = analysis.historical_summary(series)
unit = filtered["unit"].mode().iat[0]
market_label = sel["market"] or "All markets (average)"
st.write("")
fmt.kpi_cards([
    ("Average price", fmt.peso(summary["avg"]), f"per {unit.lower()}", "", "peso"),
    ("Minimum", fmt.peso(summary["min"]), fmt.month_label(summary["min_date"]), "", "down"),
    ("Maximum", fmt.peso(summary["max"]), fmt.month_label(summary["max_date"]), "", "trend"),
    ("Change over range", fmt.pct(summary["pct_change"]),
     f'{fmt.month_label(series["date"].min())} – {fmt.month_label(series["date"].max())}',
     fmt.trend_tone(summary["pct_change"]), "activity"),
])
st.write("")

ma, ma_label = None, ""
if ma_choice != "Off":
    window = int(ma_choice.split("-")[0])
    ma, ma_label = ui.moving_average(series, window), f"{ma_choice} moving average"

with fmt.card(sel["commodity"], f"{market_label} · {summary['n']:,} monthly observations"):
    fmt.show_chart(viz.price_trend_fig(series, sel["commodity"], market_label, unit, ma, ma_label),
                   key="hist_main")

with fmt.card("Trends by food category", "Uses the region, province, market and date filters above"):
    c1, c2 = st.columns([3, 1])
    all_cats = sorted(df["category"].unique())
    cats = c1.multiselect("Categories", all_cats, default=all_cats)
    mode = c2.radio("Measure", ["Index", "Average price"], horizontal=True)
    cat_df = filters.apply_filters(df, region=sel["region"], province=sel["province"],
                                   market=sel["market"], start=start, end=end)
    cat_df = cat_df[cat_df["category"].isin(cats)]
    fmt.show_chart(viz.category_trend_fig(analysis.category_series(cat_df, mode), mode), key="hist_cat")
