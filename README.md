Portfolio Analytics Dashboard
=============================

What it is
----------
A small Streamlit app to track a simple stock portfolio: add tickers (fetched from Yahoo Finance), view historical prices, and run a basic automated trading simulation.

Key pages
---------
- **View Portfolio**: chart price history for tickers in your portfolio.
- **Trading Simulation**: run a simple rule-based backtest on a selected ticker.
- **Add Ticker**: fetch historical data and add a ticker to the DB.
- **Remove Ticker**: delete tickers and their stored price data.

Run locally
-----------
1. (Optional) Create a virtual environment and activate it — not required but recommended.
2. Install dependencies:

```bash
pip install -r Requirements.txt
```

3. Start the app (recommended entrypoint preserves the app title):

```bash
streamlit run src/Trading_Portfolio_Tracker.py
```

Notes about storage
-------------------
- By default the app uses `sqlite:///portfolio_data.db` (local file) when `DATABASE_URL` is not set.
- For deployed apps on free hosts (Streamlit Community Cloud, Hugging Face Spaces) the filesystem can be ephemeral and runtime writes may be lost on restart. For durable, multi-user persistence use a managed Postgres DB and set `DATABASE_URL`.
- The app also includes client-side save/load and import/export (localStorage / JSON) for per-user storage when a server DB is not desired.

Deploying to Streamlit Community Cloud
-------------------------------------
1. Push your repository to GitHub (do NOT commit your `portfolio_venv/` folder).
2. Create a new app in Streamlit Community Cloud and point the "Main file path" to `src/Trading_Portfolio_Tracker.py`.

   Important: Streamlit installs Python packages from a file named `requirements.txt` (lowercase). If you have a file named `Requirements.txt`, also add a lowercase `requirements.txt` or rename it before deploying so dependencies are installed correctly.
3. If you want persistent server DB storage, add `DATABASE_URL` in the app's Secrets (Dashboard → Settings → Secrets) with a Postgres-style URI (Supabase/ElephantSQL/Neon).

Removing a committed venv
-------------------------
If you accidentally committed your venv, remove it from Git and push:

```bash
git rm -r --cached portfolio_venv
git commit -m "Remove venv from repo"
git push
```

Questions or next steps
-----------------------
- Wire up Postgres
- Automatic backups or an auto-save to client localStorage

Enjoy! Open an issue or ask me to add any of the above.
