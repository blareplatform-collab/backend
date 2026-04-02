# BLARE — Architecture & Folder Structure

Version: 1.0.0  
Last updated: 2026-03-29

---

## Monorepo Structure

```
blare/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
│
├── docs/
│   ├── BLARE_MASTER.md
│   ├── ARCHITECTURE.md
│   ├── BUILD_SESSIONS.md
│   └── SESSION_XX.md (one per session)
│
├── strategies/                  ← your .txt strategy library
│   ├── _template.txt
│   ├── smc_fvg_entry.txt
│   ├── smc_liquidity_sweep.txt
│   └── ...
│
├── backend/                     ← FastAPI
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   ├── config/
│   │   ├── settings.py          ← env vars, constants
│   │   └── firebase.py          ← firebase admin SDK init
│   │
│   ├── connectors/              ← one file per data source
│   │   ├── binance.py           ← crypto WebSocket + REST
│   │   ├── oanda.py             ← forex WebSocket + REST
│   │   ├── alphavantage.py      ← indices + commodities polling
│   │   └── unified.py           ← normalizes all → OHLCV format
│   │
│   ├── engine/
│   │   ├── loader.py            ← loads .txt strategy files
│   │   ├── scanner.py           ← runs rules against live data
│   │   ├── patterns/
│   │   │   ├── smc.py           ← SMC / ICT detection logic
│   │   │   ├── wyckoff.py       ← Wyckoff detection logic
│   │   │   └── classic_ta.py    ← classic chart pattern logic
│   │   └── backtest.py          ← backtesting engine
│   │
│   ├── ai/
│   │   ├── claude.py            ← Claude API calls
│   │   ├── deepseek.py          ← DeepSeek API calls
│   │   └── validator.py         ← combines AI outputs → signal
│   │
│   ├── execution/
│   │   ├── binance_orders.py    ← crypto order execution
│   │   ├── oanda_orders.py      ← forex/indices order execution
│   │   └── risk.py              ← position sizing, risk checks
│   │
│   ├── notifications/
│   │   └── fcm.py               ← Firebase Cloud Messaging
│   │
│   ├── models/
│   │   ├── signal.py            ← Signal data model
│   │   ├── trade.py             ← Trade data model
│   │   └── profile.py           ← User profile model
│   │
│   └── routes/
│       ├── signals.py           ← GET /signals
│       ├── trades.py            ← GET/POST /trades
│       ├── backtest.py          ← POST /backtest
│       ├── profiles.py          ← GET/POST /profiles
│       └── strategies.py        ← GET /strategies
│
├── frontend/                    ← shared React + Vite UI
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── i18n/
│       │   ├── en.json
│       │   ├── es.json
│       │   └── ro.json
│       ├── assets/
│       │   └── logo/            ← BLARE logo files
│       ├── components/
│       │   ├── SignalCard.jsx    ← full signal breakdown card
│       │   ├── ChartView.jsx    ← TradingView chart + overlays
│       │   ├── PatternOverlay.jsx
│       │   ├── Navbar.jsx
│       │   └── ThemeToggle.jsx
│       ├── pages/
│       │   ├── Home.jsx         ← signals feed
│       │   ├── Chart.jsx        ← chart view
│       │   ├── Positions.jsx    ← open positions + P&L
│       │   ├── Analytics.jsx    ← stats + win rate
│       │   ├── Backtest.jsx     ← backtest runner
│       │   └── Settings.jsx     ← profiles + API keys
│       ├── store/
│       │   ├── signalStore.js   ← Zustand signals state
│       │   ├── profileStore.js  ← active profile state
│       │   └── themeStore.js    ← dark/light state
│       ├── hooks/
│       │   ├── useSignals.js
│       │   └── useProfile.js
│       └── utils/
│           ├── api.js           ← axios instance → FastAPI
│           ├── format.js        ← price, date formatters
│           └── constants.js
│
├── desktop/                     ← Electron wrapper
│   ├── package.json
│   ├── electron.js              ← main process
│   ├── preload.js               ← secure IPC bridge
│   └── electron-builder.config.js
│
└── mobile/                      ← React Native + Expo
    ├── package.json
    ├── app.json
    ├── app/
    │   ├── _layout.jsx          ← Expo Router root
    │   ├── index.jsx            ← signals feed
    │   ├── positions.jsx
    │   ├── analytics.jsx
    │   └── settings.jsx
    ├── components/
    │   ├── SignalCard.jsx
    │   └── MiniChart.jsx
    └── utils/
        ├── api.js
        └── notifications.js     ← FCM setup
```

---

## Data Flow

### Live signal generation loop

```
APScheduler (every 30s)
  → connector fetches OHLCV per instrument per timeframe
  → unified.py normalizes to standard format
  → scanner.py runs all loaded strategy rules
  → pattern match found?
      YES → ai/validator.py
              → claude.py (pattern reasoning + narrative)
              → deepseek.py (confidence score 0-100)
              → risk.py (position size based on confidence)
              → Signal object created
              → saved to Firestore
              → FCM push to all user devices
              → auto mode? → execution/
      NO  → continue scanning
```

### Standard OHLCV format (unified.py output)

```python
{
  "symbol": "BTC/USDT",
  "market": "crypto",          # crypto | forex | indices | commodities
  "timeframe": "4h",
  "timestamp": 1711670400,
  "open": 67100.0,
  "high": 67580.0,
  "low": 66980.0,
  "close": 67240.0,
  "volume": 12450.5
}
```

### Signal object format

```python
{
  "id": "uuid",
  "symbol": "BTC/USDT",
  "market": "crypto",
  "direction": "long",          # long | short
  "timeframe": "4h",
  "pattern": "smc_fvg_entry",   # matches .txt filename
  "entry": 67240.0,
  "stop": 66100.0,
  "target": 69800.0,
  "rr": 2.3,
  "confidence": 84,             # DeepSeek 0-100
  "ai_note": "...",             # Claude narrative
  "position_size_pct": 2.0,     # risk.py output
  "status": "pending",          # pending | approved | rejected | executed
  "created_at": "ISO timestamp"
}
```

---

## Environment Variables

```bash
# backend/.env

# FastAPI
APP_ENV=development             # development | production
APP_PORT=8000

# Firebase
FIREBASE_PROJECT_ID=
FIREBASE_PRIVATE_KEY=
FIREBASE_CLIENT_EMAIL=

# Binance
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=true            # true for testing

# OANDA
OANDA_API_KEY=
OANDA_ACCOUNT_ID=
OANDA_ENVIRONMENT=practice      # practice | live

# Alpha Vantage
ALPHA_VANTAGE_API_KEY=

# AI APIs
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=

# Risk defaults
DEFAULT_RISK_PCT=1.0
MAX_DAILY_LOSS_PCT=3.0
```

---

## API Endpoints

```
GET  /health                     → server status
GET  /signals                    → list recent signals
GET  /signals/{id}               → single signal detail
POST /signals/{id}/approve       → semi-auto approve
POST /signals/{id}/reject        → semi-auto reject
GET  /trades                     → trade history
GET  /trades/open                → open positions
POST /backtest                   → run backtest
GET  /strategies                 → list loaded strategies
GET  /analytics/summary          → win rate, R:R, drawdown
GET  /analytics/confidence       → AI confidence accuracy
GET  /profiles                   → list profiles
POST /profiles                   → create profile
PUT  /profiles/{id}              → update profile
```

---

## Firebase Collections

```
users/
  {uid}/
    profile: { name, language, theme, riskSettings, alertPrefs }
    apiKeys: { binance_key, binance_secret, oanda_key } ← encrypted

signals/
  {signalId}/
    { ...full signal object }

trades/
  {tradeId}/
    { symbol, entry, exit, pnl, strategy, openedAt, closedAt }

analytics/
  {uid}/
    { winRate, avgRR, totalTrades, drawdown, confidenceAccuracy }
```

---

*Keep it clean. Keep it fast. Keep it sellable.*
