# BLARE — Build Sessions Plan

Version: 1.0.0  
Last updated: 2026-03-29

---

## Overview

10 sessions. Each session has a dedicated `SESSION_XX.md` with the full build prompt.
Sessions are designed to be self-contained — start any session fresh with just the session file.

| Session | Focus | Key output |
|---------|-------|-----------|
| 01 | Monorepo scaffold | Working skeleton, all folders, env config |
| 02 | Data pipeline | Live OHLCV from Binance + OANDA + Alpha Vantage |
| 03 | Pattern engine core | Rule loader, scanner loop, first strategy live |
| 04 | SMC / ICT detection | BOS, CHoCH, FVG, Order Blocks, liquidity sweeps |
| 05 | Wyckoff + Classic TA | Phase detection, chart patterns |
| 06 | AI validation layer | Claude narrative + DeepSeek scoring + position sizing |
| 07 | Execution engine | Binance + OANDA live orders, risk management |
| 08 | Dashboard UI | Signals feed, chart view, pattern overlays |
| 09 | Mobile app | React Native + Expo, FCM alerts, command center |
| 10 | Backtest + analytics | Historical testing, win rate, equity curve |

---

## Session 01 — Monorepo Scaffold

**Goal:** Working project skeleton with all folders, configs, and basic connectivity verified.

**Deliverables:**
- Full folder structure created (see ARCHITECTURE.md)
- FastAPI running on Railway (health endpoint live)
- React + Vite frontend running locally
- Electron wrapper booting the frontend
- Firebase project connected (Auth + Firestore initialized)
- All `.env` files configured with real keys
- Git repo initialized with clean `.gitignore`

**Key files created:**
- `backend/main.py`
- `backend/config/settings.py`
- `backend/config/firebase.py`
- `frontend/src/App.jsx`
- `desktop/electron.js`
- `desktop/preload.js`
- `.env.example`

---

## Session 02 — Data Pipeline

**Goal:** Live normalized OHLCV data flowing from all 3 sources into unified format.

**Deliverables:**
- `connectors/binance.py` — WebSocket + REST, crypto pairs
- `connectors/oanda.py` — WebSocket + REST, forex pairs
- `connectors/alphavantage.py` — polling, indices + commodities
- `connectors/unified.py` — normalizes all → standard OHLCV
- APScheduler running scan loop every 30s
- Instrument list configurable (which symbols to watch)
- Basic logging of incoming data

**Tested with:**
- BTC/USDT, ETH/USDT (Binance)
- EUR/USD, GBP/USD (OANDA)
- SPX, GOLD (Alpha Vantage)

---

## Session 03 — Pattern Engine Core

**Goal:** Rule library loading system + scanner loop running first real strategy.

**Deliverables:**
- `engine/loader.py` — reads all `.txt` files from `/strategies/`
- `engine/scanner.py` — runs loaded rules against OHLCV data
- First strategy live end-to-end (smc_fvg_entry.txt)
- Signal object created and saved to Firestore on match
- Console log + basic notification on signal fire
- `routes/strategies.py` — GET /strategies endpoint

**Key design:**
- Adding a new strategy = drop `.txt` file + restart
- Scanner is market-agnostic — same rules can run on any instrument

---

## Session 04 — SMC / ICT Detection

**Goal:** Full SMC / ICT pattern detection library.

**Deliverables:**
- `engine/patterns/smc.py` with detection functions for:
  - Break of Structure (BOS)
  - Change of Character (CHoCH)
  - Fair Value Gap (FVG) — bullish + bearish
  - Order Blocks (OB) — bullish + bearish
  - Liquidity sweeps (highs + lows)
  - Premium / Discount zones
- Each function: takes OHLCV array → returns detected pattern or None
- Unit tests for each detection function
- At least 3 SMC strategy `.txt` files in library

---

## Session 05 — Wyckoff + Classic TA

**Goal:** Wyckoff phase detection + classic chart pattern library.

**Deliverables:**
- `engine/patterns/wyckoff.py` with:
  - Accumulation phase detection (Phases A-E)
  - Distribution phase detection
  - Spring + UTAD identification
- `engine/patterns/classic_ta.py` with:
  - Head and Shoulders (regular + inverse)
  - Double top + Double bottom
  - Ascending / Descending / Symmetrical triangles
  - Rising + Falling wedges
  - Bull + Bear flags
- At least 3 Wyckoff strategy files
- At least 3 Classic TA strategy files

---

## Session 06 — AI Validation Layer

**Goal:** Claude + DeepSeek validating every signal with narrative + confidence score.

**Deliverables:**
- `ai/claude.py` — sends signal context to Claude, returns trade narrative
- `ai/deepseek.py` — sends signal context to DeepSeek, returns confidence 0-100
- `ai/validator.py` — orchestrates both, combines into final signal object
- `execution/risk.py` — position sizing based on confidence score:
  - 0-50: skip signal
  - 51-70: 0.5% risk
  - 71-85: 1.0% risk
  - 86-100: 1.5% risk
- Claude system prompt engineered for trading context
- DeepSeek prompt engineered for fast binary scoring

**Claude prompt context includes:**
- Current signal data (pattern, symbol, timeframe)
- Last 50 candles OHLCV
- HTF bias (daily + weekly trend)
- Active strategy rules from .txt file
- Recent signals on same instrument

---

## Session 07 — Execution Engine

**Goal:** Live order execution on Binance (crypto) and OANDA (forex/indices).

**Deliverables:**
- `execution/binance_orders.py`:
  - Market + limit orders
  - Stop loss + take profit
  - Position tracking
  - Testnet mode
- `execution/oanda_orders.py`:
  - Market + limit orders
  - Stop loss + take profit
  - Practice account mode
- Full auto mode: signal approved → order fires
- Semi-auto mode: signal → FCM alert → user taps approve → order fires
- `routes/signals.py` — POST /signals/{id}/approve + /reject
- Daily loss limit check before every order
- All trades logged to Firestore

---

## Session 08 — Dashboard UI

**Goal:** Full polished desktop + web UI — hybrid clean/deep design.

**Deliverables:**
- `pages/Home.jsx` — signals feed with full signal cards
- `components/SignalCard.jsx` — full breakdown (pattern, AI note, confidence, R:R)
- `pages/Chart.jsx` — TradingView Lightweight Charts
- `components/PatternOverlay.jsx` — FVG zones, OB boxes, BOS lines on chart
- `pages/Positions.jsx` — open positions + P&L
- `pages/Analytics.jsx` — win rate, R:R, drawdown, confidence accuracy charts
- `pages/Settings.jsx` — profiles, API keys, strategy toggles, language, theme
- Dark + Light theme toggle
- EN / ES / RO language switching
- Auto/semi-auto mode toggle (prominent in navbar)
- BLARE splash screen on startup

---

## Session 09 — Mobile App

**Goal:** React Native + Expo companion app — command center + alerts.

**Deliverables:**
- Expo Router navigation setup
- `app/index.jsx` — live signals feed
- `app/positions.jsx` — open positions + P&L
- `app/analytics.jsx` — key stats
- `app/settings.jsx` — profile + API keys
- `components/SignalCard.jsx` — mobile-optimized signal card
- FCM push notifications (signal alerts, trade confirmations)
- One-tap approve / reject on semi-auto signals
- Dark + light theme
- EN / ES / RO language support

---

## Session 10 — Backtest + Analytics

**Goal:** Historical strategy testing + full analytics dashboard.

**Deliverables:**
- `engine/backtest.py`:
  - Fetch historical OHLCV for any instrument + date range
  - Run any strategy against historical data
  - Return: win rate, avg R:R, max drawdown, total trades, equity curve
- `routes/backtest.py` — POST /backtest endpoint
- `pages/Backtest.jsx` — backtest runner UI:
  - Select strategy + market + instrument + date range
  - Run button → progress indicator
  - Results: stats table + equity curve chart
- `pages/Analytics.jsx` — completed:
  - Win rate per strategy (bar chart)
  - Drawdown history (line chart)
  - Average R:R (summary card)
  - AI confidence accuracy (scatter: confidence vs outcome)
- All analytics persisted in Firestore per user

---

## Rules for Every Session

1. Read `BLARE_MASTER.md` and `ARCHITECTURE.md` before starting
2. Never hardcode API keys
3. Every new file gets a docstring explaining its purpose
4. Every external API call wrapped in try/except
5. Test with paper/testnet accounts only until Session 10 signed off
6. Commit after every session with a clean message

---

*One session at a time. Clean and perfect.*
