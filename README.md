# Philippine Retail Food Price Dashboard

Streamlit dashboard for *Philippine Retail Food Price Trends and Forecasting Across Pre-Pandemic, Pandemic, and Post-Pandemic Periods (2016–2026)*.

**Status: frontend only.** All prices, forecasts and metrics are synthetic **DEMO DATA** (flagged on every page). Nothing shown is a research finding. The only fixed figures are the supplied dataset coverage numbers on the Overview page (`utils/config.py`).

## Run

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python -m streamlit run app.py
```

## Pages (sidebar navigation)

1. **Overview** – KPIs computed from the loaded data, price trend, period overview, price distribution, commodity insights
2. **Price Trends** – commodity/location/date filters, avg/min/max/% change, optional moving average, category trends
3. **Forecasting** – historical vs. forecast, Seasonal Naive or SARIMA, forecast direction and period
4. **Period Analysis** – Pre-Pandemic / Pandemic / Post-Pandemic averages, % change, commodity and regional comparison
5. **Model Evaluation** – actual vs. predicted, MAE / RMSE / MAPE by model and period, comparison table
6. **About** – research information

Commodity, region, market, model and horizon selections carry over between pages.

## Project layout

```
app.py                  navigation entry point
pages/                  one script per page (UI only)
utils/config.py         fixed metadata, period definitions, palette, file paths
utils/data_loader.py    load_food_price_data(): real CSV if present, else DEMO
utils/mock_data.py      ALL synthetic data lives here
utils/analysis.py       summaries, period comparison, forecast + metric retrieval
utils/filters.py        apply_filters() and sidebar filter widgets
utils/visualizations.py Plotly figure builders
utils/formatting.py     ₱ formatting, cards, KPI cards, headers
utils/theme.py          UI colour palette
utils/ui_analytics.py   display-only summaries for the UI (coverage, top movers)
assets/style.css        styling (dark sidebar, cards)
.streamlit/config.toml  theme colours
data/                   put real files here (see data/README.md)
```

## Replacing demo data with real results

1. **Prices** – copy the WFP CSV to `data/wfp_food_prices_philippines.csv`. Retail rows only are loaded. Check the `TODO(REAL DATA)` notes in `data_loader.py`.
2. **Forecasts** – write your Seasonal Naive / SARIMA outputs to `data/forecasts.csv`, or fill in `forecast_seasonal_naive()` and `forecast_sarima()` in `utils/analysis.py`.
3. **Metrics** – write evaluation results to `data/model_metrics.csv`, or edit `get_model_metrics()`.
4. **Eligibility** – replace the placeholder rule `MIN_OBS_FOR_FORECAST` in `utils/config.py` and `is_eligible_series()` in `utils/analysis.py`.

The DEMO DATA badge disappears per page once the corresponding file exists. Search the code for `TODO(REAL` to find every integration point.

## Notes

- Prices are nominal PHP, per kg except eggs (per unit). USD is not used.
- The demo food categories and commodities are placeholders; the real ones come from the WFP file.
- Demo series intentionally include gaps so the "no data" handling can be seen.
- Lower MAE, RMSE and MAPE mean better accuracy. Demo metrics are random and favour neither model.
