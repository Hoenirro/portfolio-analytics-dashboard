import streamlit as st
import pandas as pd
try:
    import plotly.graph_objects as go
    import plotly.express as px
except Exception as e:
    import streamlit as st
    st.error("Plotly is not installed in the environment. Make sure `requirements.txt` contains `plotly` and redeploy.")
    st.stop()
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker

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
st.markdown("### Price History of Your Tickers")

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

# ------------------------------------------------------------------
# Main logic
# ------------------------------------------------------------------
tickers = get_all_tickers()

if not tickers:
    st.info("No tickers in your portfolio yet. Head over to **Add Ticker** to get started!")
    st.stop()  # Stop execution here if portfolio is empty

# Prepare mappings
ticker_symbols = [t.symbol for t in tickers]
ticker_map = {t.id: t.symbol for t in tickers}           # id → symbol
symbol_to_id = {t.symbol: t.id for t in tickers}         # symbol → id

# ------------------------------------------------------------------
# Controls
# ------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.now().date() - timedelta(days=365),
        key="view_portfolio_start"
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now().date(),
        key="view_portfolio_end"
    )

selected_tickers = st.multiselect(
    "Select tickers to display:",
    options=ticker_symbols,
    default=ticker_symbols
)

if not selected_tickers:
    st.warning("Please select at least one ticker.")
    st.stop()

# ------------------------------------------------------------------
# Fetch price data
# ------------------------------------------------------------------
ids = [symbol_to_id[s] for s in selected_tickers]

session = Session()
try:
    prices = session.query(Price).filter(
        Price.ticker_id.in_(ids),
        Price.date >= start_date,
        Price.date <= end_date
    ).order_by(Price.date).all()
finally:
    session.close()

if not prices:
    st.info("No price data available for the selected tickers and date range.")
    st.stop()

# ------------------------------------------------------------------
# Group prices by ticker
# ------------------------------------------------------------------
grouped = {}
for p in prices:
    grouped.setdefault(p.ticker_id, []).append(p)

# ------------------------------------------------------------------
# Build Plotly figure
# ------------------------------------------------------------------
fig = go.Figure()
colors = px.colors.qualitative.Plotly

for idx, (ticker_id, price_list) in enumerate(grouped.items()):
    symbol = ticker_map.get(ticker_id, str(ticker_id))
    
    dates = [p.date for p in price_list]
    closes = [p.close for p in price_list]
    opens = [p.open_price or 0 for p in price_list]
    highs = [p.high or 0 for p in price_list]
    lows = [p.low or 0 for p in price_list]
    volumes = [p.volume or 0 for p in price_list]

    fig.add_trace(go.Scatter(
        x=dates,
        y=closes,
        mode='lines',
        name=symbol,
        line=dict(width=2, color=colors[idx % len(colors)]),
        hovertemplate=(
            '<b>%{x}</b><br>'
            'Close: $%{y:.2f}<br>'
            'Open: $%{customdata[0]:.2f}<br>'
            'High: $%{customdata[1]:.2f}<br>'
            'Low: $%{customdata[2]:.2f}<br>'
            'Volume: %{customdata[3]:,}<extra></extra>'
        ),
        customdata=list(zip(opens, highs, lows, volumes))
    ))

fig.update_layout(
    title="Portfolio Price History",
    xaxis_title="Date",
    yaxis_title="Price ($)",
    hovermode="x unified",
    template="plotly_white",
    height=600,
    legend_title="Tickers"
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# Optional: Show raw data table (expandable)
# ------------------------------------------------------------------
with st.expander("📋 View Raw Price Data"):
    # Convert prices to a simple DataFrame for display
    data = []
    for p in prices:
        data.append({
            "Date": p.date,
            "Ticker": ticker_map[p.ticker_id],
            "Open": p.open_price,
            "High": p.high,
            "Low": p.low,
            "Close": p.close,
            "Volume": p.volume
        })
    df = pd.DataFrame(data)
    df = df.sort_values(["Ticker", "Date"])
    st.dataframe(df, use_container_width=True)