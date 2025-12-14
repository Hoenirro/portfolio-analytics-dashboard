import sqlite3
import pandas as pd

conn = sqlite3.connect("portfolio_data.db")

print("TICKERS TABLE:")
print(pd.read_sql("SELECT * FROM tickers", conn))

print("\nPRICES TABLE (first 20 rows):")
print(pd.read_sql("SELECT * FROM prices LIMIT 20", conn))

print("\nTotal price rows:", conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0])
conn.close()