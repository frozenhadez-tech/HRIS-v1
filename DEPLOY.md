# Deploying HRPayroll L98 to Vercel + Neon

The app is a Flask app that talks to PostgreSQL. Locally it was built and fully tested
against a throwaway Postgres; production runs on **Neon** (Postgres) and **Vercel** (hosting).

## Layout
```
OLD HRIS/
├── api/index.py        # Vercel serverless entrypoint (exposes the Flask app)
├── vercel.json         # routes all traffic to the function, bundles app/**
├── requirements.txt    # Flask, psycopg, python-dotenv, Werkzeug
├── .env.example        # env-var template (never commit real .env)
└── app/                # the application
    ├── app.py  db.py  auth.py  menus.py  grids.py  payroll_engine.py
    ├── migrate.py      # SQL Server → Postgres migration
    ├── setup_auth.py   # seeds hashed login passwords
    ├── templates/  static/
```

## One-time migration (SQL Server → Neon)
Run from `app/` on the machine that has the restored SQL Server database:

```bash
# point at your Neon connection string (use the *direct*, non-pooled URL for the bulk load)
python migrate.py --target "postgresql://USER:PWD@ep-xxxx.REGION.aws.neon.tech/neondb?sslmode=require"
SEED_PASSWORD="your-strong-password" DATABASE_URL="…same…" python setup_auth.py
```
`migrate.py` recreates all 101 tables and copies every row (~1.25M). `setup_auth.py` adds the
hashed `password_hash` column and seeds every user with the initial password.

## Deploy on Vercel (GitHub flow)
1. Push this repo to a **private** GitHub repository (it contains no secrets or PII — data lives in Neon — but keep it private).
2. In Vercel: **New Project → Import** the repo. Framework preset: **Other**. Root: repo root.
3. Add **Environment Variables** (Production + Preview):
   - `DATABASE_URL` — your Neon **pooled** connection string (`…-pooler…`, `sslmode=require`)
   - `SECRET_KEY` — a long random string
4. **Deploy**. Vercel builds `api/index.py` and routes all requests to it.

## After deploy
- Visit the URL → you'll hit the **login gate**. Sign in with any user ID (e.g. `RARA`) and the
  `SEED_PASSWORD` you set. **Rotate passwords after first login.**
- The app is read-only, so it's safe to share the URL with authorized staff only.

## Notes
- Use Neon's **pooled** endpoint for `DATABASE_URL` on Vercel (serverless opens many short-lived connections).
- ~442 MB of data exceeds Neon's 0.5 GB free tier — use a paid Neon plan or drop the raw
  `timecard`/`timecardtr` tables (the app only counts them).
- Statutory `ssstable` is the ~2023 SSS schedule; load the current table for 2025 accuracy
  (the engine is table-driven — see `/engine/verify`).
