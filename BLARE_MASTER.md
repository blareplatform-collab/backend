# BLARE — Master Product Bible
**Bot-powered Liquidity Analysis & Risk Execution**

Version: 1.0.0  
Status: Pre-build  
Owner: Ovi  
Last updated: 2026-03-29

---

## 1. Vision

BLARE is a fully autonomous, AI-powered multi-market trading platform that scans crypto, forex, indices, and commodities 24/7 for high-probability trading setups — detecting patterns sourced directly from real trading strategies, validated by AI, and executed automatically or with one-tap approval.

Built clean enough to use personally. Built well enough to sell.

---

## 2. Brand

| | |
|---|---|
| Name | BLARE |
| Full name | Bot-powered Liquidity Analysis & Risk Execution |
| Accent color | Teal `#1D9E75` |
| Theme | Dark + Light toggle |
| Languages | English / Spanish / Romanian |

---

## 3. Core Philosophy

- **Rule-based detection first** — deterministic pattern rules from real strategies
- **AI validates, not hallucinates** — AI confirms signals, never invents them
- **User stays in control** — full auto or semi-auto, user decides
- **Zero noise** — clean by default, deep on demand
- **Compounding edge** — more strategy `.txt` files = smarter app over time

---

## 4. Markets

| Market | Data Source | Real-time |
|--------|-------------|-----------|
| Crypto | Binance API | Yes — WebSocket |
| Forex | OANDA API | Yes — WebSocket |
| Indices | Alpha Vantage | Polling ~1min |
| Commodities | Alpha Vantage | Polling ~1min |

---

## 5. Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| API server | FastAPI (Python) |
| Hosting | Railway (~$5/mo) |
| Database | Firebase Firestore |
| Auth | Firebase Auth |
| Push notifications | Firebase Cloud Messaging |
| Scheduling | APScheduler (inside FastAPI) |

### Frontend — Shared UI
| Layer | Technology |
|-------|-----------|
| Framework | React + Vite |
| Styling | Tailwind CSS |
| Charts | TradingView Lightweight Charts |
| State | Zustand |
| i18n | i18next (EN/ES/RO) |

### Desktop
| Layer | Technology |
|-------|-----------|
| Shell | Electron |
| Notifications | Electron native OS notifications |
| Storage | Electron secure storage (API keys) |

### Web
| Layer | Technology |
|-------|-----------|
| Hosting | Firebase Hosting |
| Notifications | Web Push API (browser native) |

### Mobile
| Layer | Technology |
|-------|-----------|
| Framework | React Native + Expo |
| Notifications | Firebase Cloud Messaging |
| Navigation | Expo Router |

### AI Layer
| Model | Role |
|-------|------|
| Claude (claude-sonnet) | Pattern reasoning, trade narrative, context analysis |
| DeepSeek | Fast signal scoring, secondary validation |

---

## 6. Architecture Overview

```
DATA SOURCES
  Binance (crypto) → WebSocket real-time
  OANDA (forex)    → WebSocket real-time
  Alpha Vantage    → Polling (indices + commodities)
        ↓
UNIFIED DATA PIPELINE (FastAPI)
  Normalize all sources → standard OHLCV format
        ↓
PATTERN ENGINE
  Rule Library (.txt strategies) → detection rules
  SMC / ICT    → BOS, CHoCH, FVG, Order Blocks, Liquidity sweeps
  Wyckoff      → Accumulation / Distribution phases
  Classic TA   → H&S, wedges, triangles, double tops
        ↓
AI VALIDATION LAYER
  Claude  → pattern reasoning + full trade narrative
  DeepSeek → confidence score (0-100)
  AI decides position size based on confidence score
        ↓
SIGNAL OUTPUT
  { symbol, direction, pattern, entry, stop, target,
    R:R, confidence, AI note, timeframe, market }
        ↓
EXECUTION ENGINE
  Full auto mode  → fires immediately
  Semi-auto mode  → sends alert, waits for user tap
  Binance orders  → crypto execution
  OANDA orders    → forex/indices/commodities execution
        ↓
PLATFORMS
  Desktop (Electron)     → full trading terminal
  Web (React)            → browser access
  Mobile (RN + Expo)     → command center + alerts
```

---

## 7. Signal Card Format

Every signal BLARE produces contains:

```
SYMBOL      BTC/USDT
MARKET      Crypto
DIRECTION   LONG
TIMEFRAME   4H

PATTERN     Liquidity sweep + FVG fill
ENTRY       $67,240
STOP        $66,100
TARGET      $69,800
R:R         2.3:1

CONFIDENCE  84/100
AI NOTE     "Price swept the previous week high, 
             engineered liquidity, then closed back 
             inside range. Clean FVG left on 15m 
             aligned with 4H bullish OB. HTF bias 
             bullish above $66,500."

STRATEGY    smc_liquidity_sweep_fvg
```

---

## 8. User Profiles

Each profile stores:
- Profile name
- Binance API key + secret (encrypted)
- OANDA API key (encrypted)
- Risk settings (max % per trade, daily loss limit)
- Active strategies (which .txt rules are enabled)
- Auto/semi-auto mode toggle
- Alert preferences (desktop / push / email)
- Preferred language
- Theme preference

Stored: Electron secure storage (desktop) / Firebase (web + mobile)

---

## 9. Dashboard — Screens

### Home
- Active signals feed (full signal cards)
- Auto/semi-auto toggle
- Quick market filter (All / Crypto / Forex / Indices / Commodities)

### Chart View
- TradingView Lightweight Charts
- Pattern overlays (FVG zones, OB boxes, BOS lines)
- Signal markers on chart

### Positions
- Open positions tracker
- P&L per position

### Analytics
- Win rate per strategy
- Average R:R
- Drawdown history
- AI confidence accuracy (did high confidence = winners?)

### Backtest
- Select strategy + market + date range
- Run backtest on historical data
- Results: win rate, R:R, max drawdown, equity curve

### Settings
- Profile management
- API key configuration
- Strategy library manager (enable/disable .txt rules)
- Alert preferences
- Language + theme

---

## 10. Strategy Library

Strategies live in `/strategies/` as `.txt` files.
Each file = one named setup with precise detection rules.

Template: see `STRATEGY_TEMPLATE.md`

The pattern engine loads all `.txt` files at startup.
Adding a new strategy = drop a file + restart. No code changes needed.

---

## 11. Monetization (Future)

If sold as a SaaS product:
- Free tier: 2 markets, 3 strategies, alerts only
- Pro tier: all markets, unlimited strategies, auto-trade
- Team tier: multiple profiles, shared strategy library

Pricing target: $29-49/mo per user

---

## 12. Non-negotiables

- No hardcoded API keys — ever
- Clean folder structure from day one
- Every module documented
- Environment-based config (dev / prod)
- Error handling on every external API call
- All API keys encrypted at rest
- Proprietary license — not open source

---

## 13. Build Sessions Overview

See `BUILD_SESSIONS.md` for full detail.

| Session | Focus |
|---------|-------|
| 1 | Monorepo scaffold + all skeletons |
| 2 | Data pipeline — Binance + OANDA + Alpha Vantage |
| 3 | Pattern engine core + rule library loader |
| 4 | SMC / ICT detection rules |
| 5 | Wyckoff + Classic TA detection |
| 6 | AI validation layer — Claude + DeepSeek |
| 7 | Execution engine — Binance + OANDA orders |
| 8 | Dashboard UI — signals feed + chart view |
| 9 | Mobile app — React Native + Expo |
| 10 | Backtesting engine + analytics |

---

*BLARE — when the market speaks, BLARE is louder.*
