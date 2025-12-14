import yfinance as yf
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import IntegrityError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === DATABASE SETUP ===
import os

# Read database connection from env so deployed apps can use a managed DB (Postgres, etc.).
# Example for Streamlit Cloud / Supabase: set `DATABASE_URL` as a secret.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///portfolio_data.db")
engine = create_engine(DATABASE_URL, echo=False, future=True)
Base = declarative_base()

class Ticker(Base):
    __tablename__ = 'tickers'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    prices = relationship("Price", back_populates="ticker", cascade="all, delete-orphan")

class Price(Base):
    __tablename__ = 'prices'
    date = Column(Date, primary_key=True)
    ticker_id = Column(Integer, ForeignKey('tickers.id', ondelete='CASCADE'), primary_key=True)
    close = Column(Float, nullable=False)
    open_price = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Integer)
    ticker = relationship("Ticker", back_populates="prices")

# Create tables if not exist
Base.metadata.create_all(engine)

def fetch_and_store(tickers, start_date='2022-01-01', end_date=None):
    if isinstance(tickers, str):
        tickers = [tickers]

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Ensure tickers exist
        existing = {r[0]: r[1] for r in session.query(Ticker.symbol, Ticker.id).filter(Ticker.symbol.in_(tickers))}
        for t in tickers:
            if t not in existing:
                nt = Ticker(symbol=t)
                session.add(nt)
                session.flush()
                existing[t] = nt.id

        all_prices = []
        for symbol in tickers:
            logger.info(f"Fetching {symbol}...")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date, actions=False, auto_adjust=False)
            if hist.empty:
                logger.warning(f"No data for {symbol}")
                continue

            for date, row in hist.iterrows():
                all_prices.append(Price(
                    date=date.date(),
                    ticker_id=existing[symbol],
                    close=row['Close'],           # or row['Close'] if you prefer unadjusted
                    open_price=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    volume=int(row['Volume']) if not pd.isna(row['Volume']) else None
                ))

        if all_prices:
            # Use merge() for upsert (handles duplicates gracefully)
            for price in all_prices:
                session.merge(price)
            session.commit()
            logger.info(f"Stored/updated {len(all_prices)} price records.")
        else:
            logger.info("No price records to store.")

    finally:
        session.close()

def remove_ticker(symbols):
    """Delete one or more tickers and all their associated price records from the database."""
    if isinstance(symbols, str):
        symbols = [symbols]
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        tickers = session.query(Ticker).filter(Ticker.symbol.in_(symbols)).all()
        if tickers:
            for ticker in tickers:
                session.delete(ticker)
            session.commit()
            deleted_symbols = [t.symbol for t in tickers]
            logger.info(f"Deleted tickers: {deleted_symbols}")
        else:
            logger.warning(f"No tickers found: {symbols}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting tickers: {e}")
        raise
    finally:
        session.close()

# === TEST ===
if __name__ == "__main__":
    test_tickers = ["AAPL", "MSFT", "GOOGL", "SPY", "TLT", "GLD"]
    fetch_and_store(test_tickers, start_date="2023-01-01")
    print("Data successfully stored in portfolio_data.db")