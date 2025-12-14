from datetime import datetime, timedelta
import streamlit as st
from sqlalchemy.orm import sessionmaker
try:
    import plotly.graph_objects as go
except Exception as e:
    import streamlit as st
    st.error("Plotly is not installed in the environment. Make sure `requirements.txt` contains `plotly` and redeploy.")
    st.stop()
import pandas as pd

# Import your existing modules
from data_layer import engine, Ticker, Price
from trading_bot import run_simulation, trades_to_df, calculate_final_value

# ------------------------------------------------------------------
# Page config (optional - you can also keep it only in the main app.py)
# ------------------------------------------------------------------
st.set_page_config(page_title="Trading Simulation", layout="wide")

# ------------------------------------------------------------------
# Title for this page
# ------------------------------------------------------------------
st.title("📈 View Portfolio")
st.markdown("### Automated Trading Simulation")

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
# Main Logic
# ------------------------------------------------------------------


tickers = get_all_tickers()
if not tickers:
    st.info("No tickers in portfolio. Add one to run a simulation!")
else:
    ticker_symbols = [t.symbol for t in tickers]
    ticker_map = {t.symbol: t.id for t in tickers}

    # --- Configuration Inputs ---
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_ticker_symbol = st.selectbox("Select Ticker for Simulation:", ticker_symbols)
        initial_cash = st.number_input("Initial Cash ($)", min_value=100.0, value=10000.0, step=100.0)
        monthly_investment = st.number_input("Monthly Investment ($)", min_value=0.0, value=0.0, step=10.0)
        
    with col2:
        start_date = st.date_input("Start Date", datetime.now().date() - timedelta(days=365))
        end_date = st.date_input("End Date", datetime.now().date())
        
    with col3:
        # Trading Rules
        buy_threshold = st.number_input("Buy Threshold (% Price Growth)", value=5.0, help="Buy when price grows by more than this % in a day")
        sell_threshold = st.number_input("Sell Threshold (% Price Drop)", value=-10.0, help="Sell when price drops by more than this % in a day (use negative for drop)")
            
        # Slippage
        buy_slippage = st.number_input("Buy Slippage (%)", value=1.0, help="Bot buys 1% over market price")
        sell_slippage = st.number_input("Sell Slippage (%)", value=1.0, help="Bot sells 1% under market price")

        # NEW INPUT
        trade_percent_input = st.number_input(
            "Percentage of Cash/Shares to Trade (%)", 
            min_value=1.0, 
            max_value=100.0, 
            value=50.0, 
            step=5.0,
            help="Percentage of available cash (for Buy) or available shares (for Sell) to use in a trade."
        )

    if st.button("Run Simulation"):
        selected_ticker_id = ticker_map[selected_ticker_symbol]
        trade_percent_decimal = trade_percent_input / 100.0

        with st.spinner(f"Running simulation for {selected_ticker_symbol} from {start_date} to {end_date}..."):
            # Run the simulation
            results = run_simulation(
                ticker_id=selected_ticker_id,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                buy_threshold=buy_threshold,
                sell_threshold=sell_threshold,
                buy_slippage=buy_slippage,
                sell_slippage=sell_slippage,
                trade_percent=trade_percent_decimal,
                monthly_investment=float(monthly_investment)
            )
            
        if "error" in results:
            st.error(results["error"])
        else:
            history_df = results['history_df']
            trades_list = results['trades']
            final_cash = results['final_cash']
            final_shares = results['final_shares']
                
            final_value = calculate_final_value(history_df, final_cash, final_shares)

            st.success("Simulation Complete!")

            # --- Results Summary ---
            st.markdown("### 📈 Simulation Summary")
            summary_cols = st.columns(5)
                
            # Calculate initial and final value for comparison (initial value is just initial_cash if no starting shares)
            initial_value = initial_cash

            summary_cols[0].metric("Initial Value", f"${initial_value:,.2f}")
            summary_cols[1].metric("Final Portfolio Value", f"${final_value:,.2f}", 
                                    delta=f"{(final_value - initial_value):,.2f}")
            summary_cols[2].metric("Final Cash Balance", f"${final_cash:,.2f}") # <--- NEW
            final_asset_value = final_value - final_cash
            summary_cols[3].metric("Final Stock Value", f"${final_asset_value:,.2f}") # <--- NEW
            summary_cols[4].metric("Total Trades", len(trades_list))
            # total deposits
            trades_df = trades_to_df(trades_list)
            deposits_df = trades_df[trades_df['Action'] == 'DEPOSIT'] if not trades_df.empty else pd.DataFrame()
            total_deposits = deposits_df['Cash Change'].sum() if not deposits_df.empty else 0.0
            st.markdown(f"**Monthly deposit:** ${monthly_investment:,.2f} — Total deposited: ${total_deposits:,.2f}")
                
            # --- Price History & Trades Graph ---
            fig = go.Figure()
                
            # Add Portfolio Value line
            fig.add_trace(go.Scatter(
                x=history_df['Date'],
                y=history_df['Portfolio Value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(width=3, color='blue')
            ))

            # Add Asset Price line (on a secondary y-axis if needed, but for simplicity, let's keep them on one)
            fig.add_trace(go.Scatter(
                x=history_df['Date'],
                y=history_df['Price'],
                mode='lines',
                name=f'{selected_ticker_symbol} Price',
                line=dict(width=1, color='gray', dash='dot')
            ))

            # Add trade markers
            trades_df = trades_to_df(trades_list)
            if not trades_df.empty:
                buy_trades = trades_df[trades_df['Action'] == 'BUY']
                sell_trades = trades_df[trades_df['Action'] == 'SELL']

                # Buy markers (Green Up Arrow)
                fig.add_trace(go.Scatter(
                    x=buy_trades['Date'],
                    y=buy_trades['Price'],
                    mode='markers',
                    name='Buy Trade',
                    marker=dict(symbol='triangle-up', size=10, color='green')
                ))
                    
                # Sell markers (Red Down Arrow)
                fig.add_trace(go.Scatter(
                    x=sell_trades['Date'],
                    y=sell_trades['Price'],
                    mode='markers',
                    name='Sell Trade',
                    marker=dict(symbol='triangle-down', size=10, color='red')
                ))

            fig.update_layout(
                title=f"Simulation History: {selected_ticker_symbol}",
                xaxis_title="Date",
                yaxis_title="Value / Price ($)",
                hovermode='x unified',
                template='plotly_white',
                height=560
            )
                
            st.plotly_chart(fig, use_container_width=True)

            # --- Detailed History ---
            st.markdown("### 📋 Trade Log")
            st.dataframe(trades_df.sort_values(by='Date', ascending=False), use_container_width=True)