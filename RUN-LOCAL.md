# Run with local PostgreSQL and a development login

This checkout uses `APP_STORAGE=postgres` in `backend/.env` and `NEXT_PUBLIC_APP_STORAGE=postgres` in `frontend/.env.local`. The old login bypass flags are disabled. PostgreSQL runs at localhost:5432 with database `humanizer` and user `postgres`. Passwords and AI keys live only in the backend environment file. AI calls use provider credits.

The fixed development account uses `APP_LOGIN_EMAIL` and `APP_LOGIN_PASSWORD`. These are separate from `POSTGRES_PASSWORD`. No Supabase account or Google login is involved. Enter the app password in the login form; it is no longer embedded in the frontend bundle.

Backend, in PowerShell:

```powershell
cd C:\Users\user\Desktop\Humanizer\Humanizer-AI\backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, in a second PowerShell terminal:

```powershell
cd C:\Users\user\Desktop\Humanizer\Humanizer-AI\frontend
npm.cmd run dev -- --hostname 127.0.0.1
```

Open http://localhost:3000/login. Sign in, choose Ghost 1 (DeepSeek) or Ghost 2 (Claude), paste text, then click Humanize. Use `localhost` consistently in browser and API URLs so the session cookie is shared.

Startup creates the additive `humanizer_app_users`, `humanizer_app_history` and `humanizer_app_sessions` tables if missing. Both modes are unlocked using the configured paid-tier models. History persists across restarts; the history endpoint returns the latest 20 entries. Usage is currently a cumulative development counter, displayed in both daily/monthly fields; calendar quotas and billing remain deferred.

Sessions last 12 hours and use an HttpOnly, SameSite=Lax cookie; only a token hash is stored in PostgreSQL. This remains a single-account development setup. Keep the servers on localhost; production account management and billing are future work.

From `backend`, verify configuration and create the tables:

```powershell
..\.venv\Scripts\python.exe check_postgres.py --initialize
..\.venv\Scripts\python.exe verify_postgres.py
```

The integration check creates and removes its own temporary account and rows. It mocks AI generation to verify authentication and persistence without spending API credits. Restart both servers after changing environment settings.
