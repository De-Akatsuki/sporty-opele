# Sporty-Opele Frontend

React + Vite dashboard for World Cup 2026 alternative-market predictions.

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local
```

Add your Supabase anon credentials to `.env.local`:

```
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

Apply the database schema from the repo root (`db/schema.sql`) or `frontend/supabase/migrations/20260602194059_create_sporty_opele_tables.sql`, then run the backend pipeline to populate data.

## Run

```bash
npm run dev
```

## Deploy on Vercel

This app uses **Vite**, not Create React App — do not use `react-scripts build`.

**Option A — deploy from repo root** (uses `/vercel.json`):

- Root Directory: leave empty (default)
- Framework Preset: Other (or Vite)
- Build Command: override **off** (repo `vercel.json` runs `cd frontend && npm run build`)

**Option B — deploy `frontend` only**:

- Root Directory: `frontend`
- Framework Preset: **Vite**
- Build Command: `npm run build` (or leave default)
- Output Directory: `dist`
- Install Command: `npm install`

In Project Settings → Environment Variables, add:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

If you previously set Framework to **Create React App**, change it to **Vite** or **Other** and clear any custom `react-scripts build` override.

Without Supabase env vars, the app runs in **dev mode** (no login required) but queries will fail until credentials are set.

## Pages

| Route | Data sources |
|---|---|
| `/` | `wc_fixtures`, `predictions`, `processed_features` |
| `/teams` | `wc_teams` (FootyStats aggregates) |
| `/performance` | `model_runs`, `prediction_outcomes`, `market_accuracy` view |

## Backend alignment

- Predictions use `probability` and `confidence_tier` (not `confidence`)
- Fixtures use `match_completed` and `group_name` (not `status` / `group`)
- Feature engineering output lives in `processed_features` (see `.agents/rules/feature_eng.md`)
