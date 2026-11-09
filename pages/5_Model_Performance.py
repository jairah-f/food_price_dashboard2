"""Model Evaluation - MAE / RMSE / MAPE by model and period (uses analysis.get_model_metrics)."""
import pandas as pd
import streamlit as st

from utils import analysis, filters, formatting as fmt, ui_analytics as ui, visualizations as viz
from utils.config import MODELS, PERIOD_ORDER
from utils.data_loader import forecasts_are_demo, metrics_are_demo, using_demo_data
from utils.theme import MODEL_COLORS, PERIOD_COLORS

demo = using_demo_data() or metrics_are_demo()
fmt.page_header("Model Evaluation", "Seasonal Naive vs. SARIMA · lower MAE, RMSE and MAPE mean better accuracy",
                demo=demo)
df = fmt.get_data()
if df.empty:
    fmt.empty_state("No data loaded", "Add the WFP CSV to the data folder.")
    st.stop()

with fmt.card():
    cols = st.columns(4)
    sel = filters.location_filters(df, require_market=True, show_category=False, slots=cols)
    c1, c2, c3 = st.columns(3)
    model = filters.sticky_select("Model", MODELS, "sel_model", MODELS[0], kind="radio",
                                  container=c1, horizontal=True)
    period = filters.sticky_select("Period", PERIOD_ORDER, "sel_period", PERIOD_ORDER[0], kind="radio",
                                   container=c2, horizontal=True)
    metric_label = c3.radio("Compare by", ["MAPE", "MAE", "RMSE"], horizontal=True,
                            help="Metric used for the comparison panels below.")
metric = metric_label.lower()

if not sel["market"]:
    fmt.empty_state("No market available", "Choose another commodity or region.")
    st.stop()

perf = analysis.get_model_metrics(df, sel["commodity"], sel["market"])
if perf.empty:
    fmt.empty_state("No evaluation results for this series", "Try another commodity or market.")
    st.stop()

row = perf[(perf["model"] == model) & (perf["period"] == period)]
other = perf[(perf["model"] != model) & (perf["period"] == period)]
if row.empty:
    fmt.empty_state(f"No {model} results for {period}")
    st.stop()
r = row.iloc[0]


def vs_other(m):
    """Sub-text comparing the selected model with the other model."""
    if other.empty:
        return "", ""
    diff = (r[m] / other.iloc[0][m] - 1) * 100
    return f'{diff:+.1f}% vs. {other.iloc[0]["model"]}', ("down" if diff < 0 else "up")


st.write("")
fmt.kpi_cards([
    ("MAE", fmt.peso(r["mae"]), *vs_other("mae"), "peso"),
    ("RMSE", fmt.peso(r["rmse"]), *vs_other("rmse"), "activity"),
    ("MAPE", fmt.pct(r["mape"], 2, signed=False), *vs_other("mape"), "target"),
    ("Evaluated observations", f'{int(r["n_obs"]):,}', f"{period} · {model}", "", "records"),
])
st.caption(" · ".join(f"**{k}**: {v}" for k, v in fmt.METRIC_HELP.items()))
st.write("")

title = f'{sel["commodity"]} · {sel["market"]}'
left, right = st.columns([2, 1])
with left, fmt.card("Actual vs. predicted prices", f"{title} · evaluation window", demo=demo):
    series = analysis.monthly_series(
        filters.apply_filters(df, commodity=sel["commodity"], market=sel["market"]))
    preds, actual = {}, pd.DataFrame()
    if analysis.is_eligible_series(series):
        for m in MODELS:
            back = analysis.get_forecast(series, sel["commodity"], sel["market"], m, 3)
            back = back[back["segment"] == "Backtest"]
            if len(back):
                preds[m] = back[["date", "forecast"]]
                actual = back[["date", "actual"]].rename(columns={"actual": "price"})
    fmt.legend_row([(MODEL_COLORS[m], m) for m in preds])
    fmt.show_chart(viz.actual_vs_predicted_fig(actual, preds), key="me_avp")
with right, fmt.card("Which model is more accurate?", f"Lower {metric_label} by period", demo=demo):
    best = ui.best_model_by_period(perf, metric)
    if best.empty:
        st.caption("Not enough results to compare.")
    for b in best.itertuples():
        st.markdown(
            f'<div class="winner"><div><div class="w-period"><span class="dot" '
            f'style="background:{PERIOD_COLORS[b.period]}"></span>{b.period}</div>'
            f'<div class="w-model">{b.model}</div></div>'
            f'<div class="w-gap">{b.gap_pct:.1f}% lower<br>than {b.other}</div></div>',
            unsafe_allow_html=True)

with fmt.card(f"MAE, RMSE and MAPE · {period}", "Seasonal Naive vs. SARIMA", demo=demo):
    cols = st.columns(3)
    for col, m, name in zip(cols, ["mae", "rmse", "mape"], ["MAE", "RMSE", "MAPE"]):
        with col:
            st.caption(f"**{name}** · {fmt.METRIC_HELP[name]}")
            fmt.show_chart(viz.metric_compare_bar(perf[perf["period"] == period], m), key=f"me_{m}")

left, right = st.columns([1, 1])
with left, fmt.card("Accuracy across the three periods", f"{metric_label} by model", demo=demo):
    fmt.show_chart(viz.accuracy_across_periods_fig(perf, metric), key="me_across")
with right, fmt.card("Comparison table", "Green = lowest error within each period", demo=demo):
    table = perf.rename(columns={"period": "Period", "model": "Model", "mae": "MAE", "rmse": "RMSE",
                                 "mape": "MAPE"})
    table["Period"] = pd.Categorical(table["Period"], PERIOD_ORDER, ordered=True)
    table = table.sort_values(["Period", "Model"]).reset_index(drop=True)
    table["Period"] = table["Period"].astype(str)
    cols_m = ["MAE", "RMSE", "MAPE"]

    def highlight_best(data):
        css = pd.DataFrame("", index=data.index, columns=data.columns)
        for c in cols_m:
            best_v = data.groupby("Period")[c].transform("min")
            css.loc[data[c] == best_v, c] = "background-color:#DFF1EE;font-weight:600"
        return css

    styled = (table[["Period", "Model"] + cols_m].style.apply(highlight_best, axis=None)
              .format({"MAE": "₱{:,.2f}", "RMSE": "₱{:,.2f}", "MAPE": "{:.2f}%"}))
    st.dataframe(styled, hide_index=True, **fmt.STRETCH)
