# EduTrack — Free Demo Deployment

A zero-cost setup to show the project to the owners. **Not for real student
data** — it's for demonstration only (no backups, the app sleeps when idle, and
uploaded files disappear on restart).

**Stack:** Render (free web service) + Neon (free PostgreSQL). No credit card
needed for either. Redis is skipped — the rate limiter uses in-memory storage,
which is fine for one demo instance.

> Heads-up to set expectations during the demo: a free Render service **sleeps
> after ~15 min of inactivity**, so the *first* request after idle takes ~30–60s
> to wake up. Open the site a minute before presenting.

---

## Step 1 — Create the free database (Neon)
1. Go to https://neon.tech and sign up (GitHub login is easiest).
2. **Create project** → name it `edutrack`, pick the region closest to you.
3. On the project dashboard, copy the **connection string**. It looks like:
   ```
   postgresql://user:password@ep-xxxx.region.aws.neon.tech/edutrack?sslmode=require
   ```
   Keep the `?sslmode=require` part — Neon needs it. This is your `DATABASE_URL`.

## Step 2 — Generate two secrets
Run locally (or in any Python prompt) **twice** to get two different values:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
One becomes `SECRET_KEY`, the other `JWT_SECRET_KEY` (each must be ≥32 chars).

## Step 3 — Put the code on GitHub
Push the project to a GitHub repo (the backend must be deployable). Do **not**
commit your `.env`. Render deploys from the repo.

## Step 4 — Create the web service on Render
1. Go to https://render.com and sign up (GitHub login).
2. **New → Web Service** → connect your repo.
3. Configure:
   - **Root Directory:** `backend`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --workers 2 --threads 2 --timeout 120 wsgi:app`
   - **Instance Type:** **Free**
   - **Health Check Path:** `/api/health`

## Step 5 — Add environment variables
In the service's **Environment** section, add:

| Key | Value |
|---|---|
| `FLASK_APP` | `wsgi.py` |
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | (first generated secret) |
| `JWT_SECRET_KEY` | (second generated secret) |
| `DATABASE_URL` | (Neon connection string from Step 1) |
| `CORS_ORIGINS` | your frontend URL, e.g. `https://edutrack-demo.onrender.com` |
| `FORCE_HTTPS` | `true` |
| `TRUST_PROXY` | `true` |
| `DB_POOL_SIZE` | `2` |
| `DB_MAX_OVERFLOW` | `0` |

Notes:
- `CORS_ORIGINS` **cannot be empty** — the app refuses to start without it. If you
  don't have a separate frontend yet, set it to the API's own Render URL as a
  placeholder; update it once the frontend URL is known.
- Keep the pool small — Neon's free tier allows few connections.
- Skip all `SMTP_*` for the demo. Everything works except teacher password-reset
  emails (it returns a "temporarily unavailable" message, which is fine to show).

## Step 6 — Create the database tables
After the first deploy succeeds, open the service's **Shell** tab and run:
```bash
flask db upgrade
```
Then create your first admin account with your project's admin/seed command and
confirm it:
```bash
flask list-accounts
```
(If you prefer, add `flask db upgrade` as a **Pre-Deploy Command** so it runs
automatically on every deploy.)

## Step 7 — Verify
Visit `https://YOUR-SERVICE.onrender.com/api/health` — you should see:
```json
{"status": "ok", "service": "EduTrack API", "database": "PostgreSQL"}
```
Then log in with the admin account you created.

---

## Demo-day tips
- Wake the service ~1 minute before presenting (first request is slow after idle).
- Pre-load a little sample data (a few classes, students, a teacher) so screens
  look populated.
- File uploads work during a session but vanish on restart/sleep — avoid relying
  on them, or re-upload right before the demo.
- If the owners approve, move to the paid Tier 1 or Tier 2 setup (see
  `DEPLOYMENT.md`) before handling real student data.

## Free limits to be aware of
- **Render free:** sleeps after ~15 min idle; ~512 MB RAM; shared CPU.
- **Neon free:** ~0.5 GB storage; plenty for a demo dataset; no production backups.
