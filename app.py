"""Entry point:  python -m streamlit run app.py   (unchanged entry point)

Sets up the page and the dark sidebar navigation. Page scripts live in /pages.
"""
import streamlit as st

st.set_page_config(page_title="Food Price Analytics", layout="wide",
                   initial_sidebar_state="expanded")

pages = [
    st.Page("pages/1_Overview.py", title="Overview", icon=":material/dashboard:", default=True),
    st.Page("pages/2_Historical_Trends.py", title="Price Trends", icon=":material/show_chart:"),
    st.Page("pages/4_Forecasting.py", title="Forecasting", icon=":material/query_stats:"),
    st.Page("pages/3_Period_Comparison.py", title="Period Analysis", icon=":material/timeline:"),
    st.Page("pages/5_Model_Performance.py", title="Model Evaluation", icon=":material/fact_check:"),
    st.Page("pages/6_About.py", title="About", icon=":material/info:"),
]
navigation = st.navigation(pages)

try:  # small footer in the sidebar, computed from the loaded data
    from utils import formatting as fmt
    from utils.data_loader import load_food_price_data, using_demo_data
    _df = load_food_price_data()
    _cov = f"{fmt.month_label(_df['date'].min())} – {fmt.month_label(_df['date'].max())}"
    _src = "Demo data" if using_demo_data() else "WFP Food Prices"
    st.sidebar.markdown(f'<div class="side-note"><b>{_src}</b><br>Retail prices · PHP<br>{_cov}</div>',
                        unsafe_allow_html=True)
except Exception:  # never block navigation because of the footer
    pass

navigation.run()
