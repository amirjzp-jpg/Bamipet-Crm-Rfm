# Deploying on free-tier hosting (Vercel + Render + Neon)

This is the concrete, step-by-step path to a live URL using entirely free
tiers, as an alternative to the Docker Compose deployment in the main
[`README.md`](../README.md) (which is the better choice if you have any
always-on host — a VPS, Fly.io, Railway, etc. — since it runs the real
nightly worker instead of the GitHub Actions workaround below).

**Reality check first:** Navatel credentials are the only *business* input
missing. But "launch on Vercel" alone is not enough — Vercel only hosts the
frontend. You additionally need a Postgres database and a host for the
Python backend, both outside Vercel. This guide uses Neon (database) and
Render (backend) because both have real free tiers as of 2026; the frontend
goes on Vercel as you'd expect.

```
Vercel (frontend, static)  ──calls──>  Render (backend API, Docker)  ──>  Neon (Postgres)
                                              ▲
                                              │ nightly, via HTTP
                                    GitHub Actions (cron, free)
```

## 1. Database — Neon

1. Sign up at neon.tech, create a project (any region).
2. Copy the connection string it gives you. It looks like:
   `postgresql://user:password@ep-xxxx.neon.tech/dbname?sslmode=require`
3. **Change the scheme** from `postgresql://` to `postgresql+psycopg://`
   (this app's SQLAlchemy driver) — the rest of the string stays as-is.
   That full string is your `DATABASE_URL`.

Supabase works the same way if you prefer it — same scheme adjustment.

## 2. Backend — Render

1. Push this repo to GitHub (if not already).
2. In Render: **New > Blueprint**, point it at this repo. Render reads
   [`render.yaml`](../render.yaml) at the repo root and creates the
   `bamipet-rfm-api` web service automatically (free plan, builds
   `backend/Dockerfile`).
3. In the service's **Environment** tab, fill in the variables marked
   `sync: false` in `render.yaml`:
   - `DATABASE_URL` — the Neon string from step 1
   - `BOOTSTRAP_ADMIN_USERNAME` / `BOOTSTRAP_ADMIN_PASSWORD` — your first
     admin login (used once, in step 4)
   - `CORS_ORIGINS` — leave a placeholder for now; you'll fill in your real
     Vercel URL after step 3
4. Deploy. Once it's live, open the **Shell** tab (available on the free
   plan) and run once:
   ```bash
   alembic upgrade head
   python -m scripts.create_admin
   python -m scripts.seed_demo   # optional demo data, mock mode only
   ```
5. Note your backend's URL, e.g. `https://bamipet-rfm-api.onrender.com`.

**Free-tier caveat:** Render's free web services spin down after 15 minutes
of no traffic and take ~30–60s to wake on the next request. The dashboard's
first load after idle time will be slow once — this is normal, not a bug.

## 3. Frontend — Vercel

1. In Vercel: **New Project**, import this repo, set **Root Directory** to
   `frontend/`. Vercel auto-detects Vite; [`frontend/vercel.json`](../frontend/vercel.json)
   handles the SPA routing.
2. Add an environment variable: `VITE_API_BASE_URL` = your Render URL from
   step 2.4 (no trailing slash), e.g. `https://bamipet-rfm-api.onrender.com`.
3. Deploy. Note the resulting Vercel URL, e.g. `https://bamipet-rfm.vercel.app`.
4. Back in Render, set `CORS_ORIGINS` to that Vercel URL (comma-separate if
   you have more than one, e.g. a preview + production domain) and redeploy
   the backend so the browser is allowed to call it cross-origin.

## 4. Nightly sync — GitHub Actions

Render's free tier has no always-on worker, so
[`.github/workflows/nightly-sync.yml`](../.github/workflows/nightly-sync.yml)
calls the backend's trigger endpoint on a schedule instead of running
`sync/worker.py` continuously. Add these repo secrets (**Settings > Secrets
and variables > Actions**):

- `BAMIPET_API_URL` — your Render URL
- `BAMIPET_ADMIN_USERNAME` / `BAMIPET_ADMIN_PASSWORD` — the admin account
  from step 2.4

The workflow runs nightly and can also be fired manually from the **Actions**
tab (**Run workflow**) to test it immediately.

## Result

- Dashboard: your Vercel URL
- API docs: `<your Render URL>/api/docs`
- Total monthly cost: **$0**, with the tradeoffs above (Render cold starts,
  GitHub Actions instead of a true background worker).

## Going live with real Navatel data

Same as the main README: set `NAVATEL_MODE=live` plus the base URL, token,
endpoint paths, and field aliases in Render's Environment tab (all pulled
from the Swagger docs behind login at `cp.navatel.ir`), then redeploy.
