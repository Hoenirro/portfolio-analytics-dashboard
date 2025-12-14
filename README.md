Deploying to Streamlit Community Cloud
-------------------------------------

1. Push your repository to GitHub (do NOT commit your `portfolio_venv/` folder).

2. Ensure `Requirements.txt` lists your Python dependencies (it already does).

3. In Streamlit Community Cloud, create a new app and connect your GitHub repo. For the "Main file path" enter `src/app.py` (or the path you run locally).

4. To persist to an external DB (recommended), set a `DATABASE_URL` secret in the Streamlit app settings (Dashboard → "Secrets"). Example (Postgres/Supabase):

   DATABASE_URL = "postgres://user:pass@host:5432/dbname"

   - If you don't set `DATABASE_URL`, the app will fall back to a local `sqlite:///portfolio_data.db` file (which is ephemeral on many free hosts).

5. If you committed a venv folder, remove it from the repo with:

```bash
git rm -r --cached portfolio_venv
git commit -m "Remove venv from repo"
git push
```

Notes
- Streamlit Community Cloud will install packages from `Requirements.txt` automatically; you don't need to provide a `bat` file to create a venv.
- Free hosts often put apps to sleep on inactivity and ephemeral files (like SQLite DB) may be lost on restart or redeploy — use a managed DB for persistence.
