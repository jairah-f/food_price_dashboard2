"""About - research information."""
import streamlit as st

from utils import formatting as fmt
from utils.config import METADATA, PERIOD_RANGE_LABELS, WHOLESALE_EXCLUDED

fmt.page_header("About the Research", "Study information and dataset rules", demo=False)

with fmt.card("Research title", demo=False):
    st.markdown('<div class="about"><p>Philippine Retail Food Price Trends and Forecasting Across '
                'Pre-Pandemic, Pandemic, and Post-Pandemic Periods (2016–2026)</p></div>',
                unsafe_allow_html=True)

left, right = st.columns(2)
with left, fmt.card("Objectives", demo=False):
    st.markdown("""<div class="about"><ol>
<li>Analyze historical food-price trends across commodities, food categories, markets, and regions.</li>
<li>Compare retail price levels and percentage changes across the three periods.</li>
<li>Apply Seasonal Naive and SARIMA models and evaluate them with MAE, RMSE, and MAPE.</li>
<li>Provide an interactive dashboard for price monitoring.</li></ol></div>""", unsafe_allow_html=True)
with right, fmt.card("Study periods", demo=False):
    rows = "".join(f"<tr><td>{p}</td><td>{r}</td></tr>" for p, r in PERIOD_RANGE_LABELS.items())
    st.markdown(f'<table class="meta-table">{rows}</table>', unsafe_allow_html=True)

left, right = st.columns(2)
with left, fmt.card("Dataset", "World Food Programme (WFP) Food Prices – Philippines", demo=False):
    rows = [(k, v) for k, v in METADATA.items()] + [
        ("Price type", "Retail only"),
        ("Excluded", f"{WHOLESALE_EXCLUDED} wholesale records (kept in the file)"),
        ("Currency", "Nominal PHP (USD supplementary)"),
        ("Unit", "Per kg; eggs per unit")]
    st.markdown('<table class="meta-table">' + "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows) + "</table>", unsafe_allow_html=True)
    st.caption("Coverage figures above are the study's reference metadata. The Overview page "
               "computes its numbers from the data actually loaded.")
with right, fmt.card("Metrics", demo=False):
    st.markdown("""<div class="about"><ul>
<li><b>MAE</b> – average size of the forecast error, in pesos.</li>
<li><b>RMSE</b> – like MAE, but large misses count more.</li>
<li><b>MAPE</b> – average error as a percentage of the actual price.</li></ul>
<p>Lower values mean better accuracy. Neither model is assumed to be better.</p></div>""",
                unsafe_allow_html=True)
