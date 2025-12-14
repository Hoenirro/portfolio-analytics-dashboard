from datetime import datetime, timedelta
import streamlit as st
from sqlalchemy.orm import sessionmaker
from data_layer import fetch_and_store

# Import your existing modules
from data_layer import engine, Ticker, Price

# ------------------------------------------------------------------
# Page config (optional - you can also keep it only in the main app.py)
# ------------------------------------------------------------------
st.set_page_config(page_title="View Portfolio", layout="wide")

# ------------------------------------------------------------------
# Title for this page
# ------------------------------------------------------------------
st.title("📈 View Portfolio")
st.markdown("### Add New Ticker to Your Portfolio")

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

col1, col2 = st.columns(2)
with col1:
    ticker_input = st.text_input("Ticker Symbol (e.g., AAPL)").upper()
    start_date = st.date_input("Start Date", datetime.now().date() - timedelta(days=365))
with col2:
    end_date = st.date_input("End Date", datetime.now().date())

if st.button("Fetch & Add"):
    if not ticker_input:
        st.warning("Please enter a ticker symbol")
    else:
        with st.spinner(f"Fetching {ticker_input} data..."):
            try:
                fetch_and_store(ticker_input, start_date=str(start_date), end_date=str(end_date))
                st.success(f"✅ {ticker_input} added successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")