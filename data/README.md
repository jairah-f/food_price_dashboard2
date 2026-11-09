# Data folder

The dashboard runs without any file here (DEMO DATA). To switch to real results, add the files below.
Each one is independent, so you can add them as the analysis progresses.

| File | Replaces | Required columns |
|---|---|---|
| `wfp_food_prices_philippines.csv` | demo price panel | Raw WFP export: `date, admin1, admin2, market, category, commodity, unit, pricetype, currency, price` (the HXL tag row is skipped automatically) |
| `forecasts.csv` | demo forecasts | `commodity, market, model, date, forecast, lower, upper` (optional: `actual`, `segment` = `Backtest` or `Forecast`) |
| `model_metrics.csv` | demo metrics | `commodity, market, period, model, mae, rmse, mape, n_obs` |

Notes
- Only `Retail` rows are used. The 2,615 wholesale records can stay in the file; they are filtered out on load.
- Prices are nominal PHP (per kg; eggs per unit). `usdprice` is ignored.
- `model` values: `Seasonal Naive`, `SARIMA`. `period` values: `Pre-Pandemic`, `Pandemic`, `Post-Pandemic`.
- `admin1` is mapped to region and `admin2` to province in `utils/data_loader.py` (check against the final file).
- The default commodity is `Rice (Regular Milled)` (`utils/config.py`). If the real file spells it differently, update `DEFAULT_COMMODITY`.
