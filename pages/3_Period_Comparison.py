"""Period Analysis - Pre-Pandemic vs. Pandemic vs. Post-Pandemic."""
import streamlit as st

from utils import analysis, filters, formatting as fmt, ui_analytics as ui, visualizations as viz
from utils.config import PERIOD_ORDER, PERIOD_RANGE_LABELS

fmt.page_header("Period Analysis", "How retail prices changed across the three study periods")
df = fmt.get_data()
if df.empty:
    fmt.empty_state("No data loaded", "Add the WFP CSV to the data folder.")
    st.stop()

with fmt.card():
    cols = st.columns([2, 2, 2, 3])
    sel = filters.location_filters(df, show_province=False, show_market=False, slots=cols[:3])
    periods = cols[3].multiselect("Periods", PERIOD_ORDER, default=PERIOD_ORDER)
if not periods:
    fmt.empty_state("Select at least one period")
    st.stop()

data = filters.apply_filters(df, category=sel["category"], commodity=sel["commodity"], region=sel["region"])
if data.empty:
    fmt.empty_state("No observations for this selection", "Try another commodity or region.")
    st.stop()

# Availability check (placeholder: counts rows per period, not per commodity-market series).
avail = analysis.period_availability(data)
missing = [p for p in periods if avail[p] == 0]
if missing:
    st.info("No observations in: " + ", ".join(missing))

summary = analysis.period_summary(data, periods)
changes = analysis.period_changes(summary)
st.write("")
fmt.kpi_cards([(r.period, fmt.peso(r.avg_price), f"{PERIOD_RANGE_LABELS[r.period]} · {r.n_obs:,} obs",
                "", "calendar") for r in summary.itertuples()])
st.write("")

c1, c2 = st.columns(2)
with c1, fmt.card("Average retail price", "Mean price in each period"):
    fmt.show_chart(viz.period_avg_bar(summary), key="pc_avg")
with c2, fmt.card("Change between periods", "Percentage change in average price"):
    fmt.show_chart(viz.period_change_bar(changes), key="pc_chg")

with fmt.card("Price trend by period", f'{sel["commodity"]} · {sel["region"] or "All regions"}'):
    fmt.show_chart(viz.trend_shading_fig(analysis.monthly_series(data), periods), key="pc_trend")

with fmt.card("Commodity comparison", "Change in average price for every commodity (all regions)"):
    table = ui.commodity_period_table(filters.apply_filters(df, category=sel["category"]))
    fmt.show_chart(viz.commodity_change_fig(table), key="pc_commodity")
    with st.expander("Show table"):
        if table.empty:
            st.caption("No data.")
        else:
            show = table.rename(columns={"commodity": "Commodity", "pre_to_pandemic": "Pre → Pandemic",
                                         "pandemic_to_post": "Pandemic → Post"})
            st.dataframe(show.style.format({**{p: "₱{:,.2f}" for p in PERIOD_ORDER},
                                            "Pre → Pandemic": "{:+.1f}%", "Pandemic → Post": "{:+.1f}%"},
                                           na_rep="—"), hide_index=True, **fmt.STRETCH)

with fmt.card("Regional comparison", f'{sel["commodity"]} · average price by region and period'):
    regional = filters.apply_filters(df, category=sel["category"], commodity=sel["commodity"])
    fmt.show_chart(viz.regional_comparison_fig(analysis.regional_period_summary(regional, periods)),
                   key="pc_region")
