# Session 1: Scaffold + Skeletons

**Date:** 2026-03-29
**Status:** Completed

## Objectives
- [x] Create monorepo folder and file architecture as specified in `ARCHITECTURE.md`.
- [x] Setup Python backend skeleton (FastAPI, requirements, `main.py`, models, settings).
- [x] Setup React frontend skeleton (Vite, Tailwind, generic `App.jsx`, `package.json`).
- [x] Install frontend NPM dependencies.
- [x] Create Python virtual environment and install backend dependencies.

## Key Decisions
- Placed all frontend React source code inside `frontend/src`.
- Used Vite for fast frontend loading. Tailwind CSS initialized.
- Setup `pydantic-settings` to manage environment variables gracefully in the backend. 
- Created `Signal` model leveraging UUIDs and `pydantic`.

## Next Session (Session 2)
Focus on building the Data Pipeline — connecting Binance, OANDA, and Alpha Vantage APIs to stream live data into a unified OHLCV format.
