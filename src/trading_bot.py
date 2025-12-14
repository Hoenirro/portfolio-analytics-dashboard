import pandas as pd
from data_layer import engine, Price
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
from typing import List, Dict, Any

Session = sessionmaker(bind=engine)

# Define a class for the trade records for clarity
class Trade:
    def __init__(self, date: date, action: str, shares: float, price: float, cash_change: float):
        self.date = date
        self.action = action  # 'BUY' or 'SELL'
        self.shares = shares
        self.price = price
        self.cash_change = cash_change

    def to_dict(self) -> Dict[str, Any]:
        return {
            'Date': self.date,
            'Action': self.action,
            'Shares': self.shares,
            'Price': self.price,
            'Cash Change': self.cash_change
        }

def run_simulation(
    ticker_id: int,
    start_date: date,
    end_date: date,
    initial_cash: float,
    buy_threshold: float,
    sell_threshold: float,
    buy_slippage: float,
    sell_slippage: float,
    trade_percent: float,
    monthly_investment: float = 0.0,
) -> Dict[str, Any]:
    """
    Runs a trading simulation based on simple percentage-based rules.
    
    Returns: A dictionary with 'history_df' (portfolio value/cash/shares over time) 
             and 'trades' (list of Trade objects).
    """
    session = Session()
    try:
        # 1. Fetch Price Data
        prices_db = session.query(Price).filter(
            Price.ticker_id == ticker_id,
            Price.date >= start_date,
            Price.date <= end_date
        ).order_by(Price.date).all()
    finally:
        session.close()

    if not prices_db:
        return {"error": "No price data available for the selected ticker and date range."}

    # Validate monthly_investment
    if monthly_investment < 0:
        raise ValueError("monthly_investment must be non-negative")

    # Convert to DataFrame for easier manipulation and adding calculated fields
    prices = pd.DataFrame([
        {'date': p.date, 'close': p.close, 'open': p.open_price, 'high': p.high, 'low': p.low} 
        for p in prices_db
    ])
    prices.set_index('date', inplace=True)
    
    # Calculate daily percentage change
    prices['pct_change'] = prices['close'].pct_change() * 100

    # 2. Initialize Portfolio
    cash = initial_cash
    shares = 0.0
    trades: List[Trade] = []
    history: List[Dict[str, Any]] = []
    
    # Track the last investment date so we deposit on the first trading day of a new month
    last_investment_date = start_date - timedelta(days=31)

    # 3. Run Simulation Day by Day
    for current_date, row in prices.iterrows():
        close_price = row['close']
        daily_pct_change = row['pct_change']
        
        # --- Monthly Investment (Revised Logic) ---
        # Deposit once per calendar month on the first observed trading day for that month.
        if monthly_investment > 0 and (current_date.year, current_date.month) != (last_investment_date.year, last_investment_date.month):
            cash += monthly_investment
            last_investment_date = current_date
            trades.append(Trade(current_date, 'DEPOSIT', 0.0, close_price, monthly_investment))

        # --- Calculate Current Value ---
        asset_value = shares * close_price
        portfolio_value = cash + asset_value
        
        history.append({
            'Date': current_date,
            'Cash': cash,
            'Shares': shares,
            'Asset Value': asset_value,
            'Portfolio Value': portfolio_value,
            'Price': close_price
        })

        # Skip the first day as pct_change is NaN
        if pd.isna(daily_pct_change):
            continue

        # --- Trading Logic ---
        
        # BUY signal: Price grew over the threshold
        if daily_pct_change > buy_threshold:
            # Calculate actual buy price with slippage
            buy_price = close_price * (1 + buy_slippage / 100)
            
            # Amount to spend: trade_percent of current cash
            amount_to_spend = cash * trade_percent
            
            # Shares to buy
            shares_to_buy = amount_to_spend / buy_price
            
            if shares_to_buy * buy_price <= cash:
                cash -= shares_to_buy * buy_price
                shares += shares_to_buy
                trades.append(Trade(current_date, 'BUY', shares_to_buy, buy_price, -(shares_to_buy * buy_price)))

        # SELL signal: Price fell below the threshold (or negative threshold)
        elif daily_pct_change < sell_threshold:
            # Calculate actual sell price with slippage
            sell_price = close_price * (1 - sell_slippage / 100)
            
            # Shares to sell: trade_percent of current shares
            shares_to_sell = shares * trade_percent
            
            if shares_to_sell > 0:
                cash += shares_to_sell * sell_price
                shares -= shares_to_sell
                trades.append(Trade(current_date, 'SELL', shares_to_sell, sell_price, shares_to_sell * sell_price))

    # Final History DataFrame
    history_df = pd.DataFrame(history)
    history_df['Date'] = pd.to_datetime(history_df['Date'])

    # Calculate final asset value based on the final price
    final_asset_value = history_df['Price'].iloc[-1] * shares
    
    return {
        'history_df': history_df, 
        'trades': [t.to_dict() for t in trades],
        'final_cash': cash,
        'final_shares': shares,
        'final_asset_value': final_asset_value
    }

# Convert Trade list to a DataFrame for display
def trades_to_df(trades: List[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(trades)

# Function to calculate final value (assuming the last recorded price is the current price)
def calculate_final_value(history_df: pd.DataFrame, final_cash: float, final_shares: float) -> float:
    if history_df.empty:
        return final_cash
    last_price = history_df['Price'].iloc[-1]
    return final_cash + (final_shares * last_price)