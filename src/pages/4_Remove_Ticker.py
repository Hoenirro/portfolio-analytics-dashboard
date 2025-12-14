import streamlit as st
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Import your existing modules
from data_layer import engine, Ticker, remove_ticker

# ------------------------------------------------------------------
# Page config (optional - you can also keep it only in the main app.py)
# ------------------------------------------------------------------
st.set_page_config(page_title="Trading Simulation", layout="wide")

# ------------------------------------------------------------------
# Title for this page
# ------------------------------------------------------------------
st.title("📈 View Portfolio")
st.markdown("### Remove Ticker from Your Portfolio")

# ------------------------------------------------------------------
# Database session helper
# ------------------------------------------------------------------
Session = sessionmaker(bind=engine)

def get_all_tickers():
    session = Session()
    try:
        tickers = session.query(Ticker).order_by(Ticker.symbol).all()
        return tickers
    finally:
        session.close()

tickers = get_all_tickers()
if not tickers:
    st.info("No tickers to remove")
else:
    ticker_symbols = [t.symbol for t in tickers]
    selected = st.multiselect("Select tickers to remove:", ticker_symbols)

    if st.button("Remove Selected"):
        if not selected:
            st.warning("No tickers selected")
        else:
            with st.spinner("Removing tickers..."):
                try:
                    remove_ticker(selected)
                    st.success(f"✅ Removed: {', '.join(selected)}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")