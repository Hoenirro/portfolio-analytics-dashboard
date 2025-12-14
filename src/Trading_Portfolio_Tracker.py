import streamlit as st

# This sets the title, icon, and layout for the entire app
st.set_page_config(
    page_title="Portfolio Analytics",
    page_icon="📊",
    layout="wide"
)

# Homepage content (shown when user first opens the app)
st.title("📊 Portfolio Analytics Dashboard")
st.markdown(
    """
    Welcome to your personal stock portfolio tool!  
    Use the navigation menu on the left to:
    
    📈 **View Portfolio** – See price charts for all your stocks  
    🤖 **Trading Simulation** – Test automated buy/sell strategies  
    ➕ **Add Ticker** – Download and add new stocks  
    ❌ **Remove Ticker** – Clean up your portfolio  
    
    **Get started:** Add a ticker like AAPL or TSLA, then explore the charts and simulations!
    """
)

# Optional: Quick stats (feels like a real dashboard)
st.sidebar.success("Select a page from the menu above ↑")

# Optional fun touch: show how many tickers are in the portfolio right on the homepage
try:
    from data_layer import engine, Ticker
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()
    ticker_count = session.query(Ticker).count()
    session.close()

    if ticker_count > 0:
        st.sidebar.metric("Tickers in Portfolio", ticker_count)
    else:
        st.sidebar.info("No tickers yet – add your first one!")
except Exception:
    # If something goes wrong (e.g., database not ready), just skip the count
    pass

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit • Data powered by Yahoo Finance")

with st.sidebar.expander("Diagnostics"):
    import sys
    import importlib
    import importlib.metadata
    st.write(f"Python: {sys.version.splitlines()[0]}")

    # Check for key package(s)
    try:
        plotly_ver = importlib.metadata.version('plotly')
        st.success(f"plotly installed: {plotly_ver}")
    except importlib.metadata.PackageNotFoundError:
        st.error("plotly is NOT installed in this environment.")

    # Show requirements.txt if present
    try:
        with open('requirements.txt', 'r') as f:
            reqs = f.read().strip()
        st.markdown("**requirements.txt:**")
        st.text(reqs or "(file is empty)")
    except FileNotFoundError:
        st.write("requirements.txt not found in repo root on the running instance.")