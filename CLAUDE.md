# LoL Match Analyzer

## Project Overview
A web app that analyzes League of Legends matches to identify momentum shifts, correlate them with game events, and generate natural language insights explaining why you won or lost.

## Stack
- **Backend:** Python 3.12+, FastAPI, httpx (async), aiosqlite, pydantic
- **Frontend:** React 18 + TypeScript, Vite, Tailwind CSS, Recharts, TanStack Query
- **No external infra:** SQLite for persistent cache, in-memory for volatile cache

## Project Structure
- `backend/app/` — FastAPI application
  - `routers/` — API endpoints (summoner, matches, analysis)
  - `schemas/` — Pydantic response models
  - `services/` — Riot API client, match service, analysis engine
  - `analysis/` — Core algorithms (gold analysis, momentum detection, event correlation, insight generation)
  - `cache/` — SQLite persistent cache + in-memory TTL cache
- `frontend/src/` — React application
  - `pages/` — HomePage (search), PlayerPage (history), MatchAnalysisPage (dashboard)
  - `components/analysis/` — GoldDiffChart, InsightCards, ObjectiveTimeline, KillTimeline, PlayerStatsTable
  - `api/` — Fetch client, endpoint functions, TypeScript types
  - `hooks/` — TanStack Query hooks

## Riot API Details
- Region: NA (platform: `na1`, regional: `americas`)
- Account/Match-v5 endpoints use `americas.api.riotgames.com`
- Summoner endpoints use `na1.api.riotgames.com`
- Dev key rate limits: 20 req/sec, 100 req/2min
- Match/timeline data is immutable — cache forever in SQLite

## Running
```bash
# Backend
cd backend && pip install -r requirements.txt
cp ../.env.example ../.env  # Add your RIOT_API_KEY
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Key Conventions
- All Riot API calls go through `services/riot_api.py` (never call httpx directly elsewhere)
- Analysis modules are pure functions — they take data in, return results (no side effects)
- Pydantic schemas in `schemas/` define the API contract between backend and frontend
- Frontend TypeScript types in `api/types.ts` must mirror backend schemas
- Use `asyncio.gather` for parallel API calls but respect rate limits via the semaphore in riot_api.py
