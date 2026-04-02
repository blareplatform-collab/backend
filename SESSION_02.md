# BLARE — Session 02: Data Pipeline

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to build
Prerequisite: Session 01 complete

---

## Context

Read `BLARE_MASTER.md` and `ARCHITECTURE.md` before starting.

This session builds the entire data layer — live OHLCV from all 3 sources,
normalized into one unified format the pattern engine will consume.
By the end, live candle data is flowing from Binance, OANDA, and Alpha Vantage
into a single clean pipeline.

---

## Goals

- [ ] Binance WebSocket streaming live crypto candles
- [ ] OANDA WebSocket streaming live forex candles
- [ ] Alpha Vantage polling indices + commodities every 60s
- [ ] All data normalized to unified OHLCV format
- [ ] APScheduler scan loop running every 30s
- [ ] Instrument list configurable via settings
- [ ] Basic logging showing live data flow
- [ ] GET /candles/{symbol} endpoint working

---

## Step 1 — Binance connector

### backend/connectors/binance.py
```python
"""
BLARE Binance Connector
Fetches live and historical OHLCV data for crypto pairs.
Supports WebSocket streaming and REST polling.
"""
import asyncio
import json
import websockets
import httpx
from datetime import datetime
from config.settings import BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_TESTNET
from connectors.unified import normalize_candle

BASE_URL = "https://testnet.binance.vision" if BINANCE_TESTNET else "https://api.binance.com"
WS_BASE = "wss://testnet.binance.vision/ws" if BINANCE_TESTNET else "wss://stream.binance.com:9443/ws"

# In-memory candle store: { "BTCUSDT_1h": [candle, candle, ...] }
candle_store = {}

TIMEFRAME_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m",
    "1h": "1h", "4h": "4h", "1d": "1d"
}

async def fetch_historical(symbol: str, timeframe: str, limit: int = 200) -> list:
    """Fetch historical OHLCV candles from Binance REST API."""
    try:
        url = f"{BASE_URL}/api/v3/klines"
        params = {"symbol": symbol, "interval": TIMEFRAME_MAP[timeframe], "limit": limit}
        async with httpx.AsyncClient() as client:
            res = await client.get(url, params=params, timeout=10)
            res.raise_for_status()
            raw = res.json()
            candles = [normalize_candle({
                "symbol": symbol.replace("USDT", "/USDT"),
                "market": "crypto",
                "timeframe": timeframe,
                "timestamp": int(c[0] / 1000),
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": float(c[5]),
            }) for c in raw]
            key = f"{symbol}_{timeframe}"
            candle_store[key] = candles
            print(f"[Binance] Loaded {len(candles)} candles for {symbol} {timeframe}")
            return candles
    except Exception as e:
        print(f"[Binance] fetch_historical error {symbol}: {e}")
        return []

async def stream_candles(symbol: str, timeframe: str, on_candle=None):
    """Stream live candles via Binance WebSocket."""
    stream = f"{symbol.lower()}@kline_{TIMEFRAME_MAP[timeframe]}"
    uri = f"{WS_BASE}/{stream}"
    print(f"[Binance] Starting stream: {stream}")
    while True:
        try:
            async with websockets.connect(uri) as ws:
                async for message in ws:
                    data = json.loads(message)
                    k = data.get("k", {})
                    if k.get("x"):  # candle closed
                        candle = normalize_candle({
                            "symbol": symbol.replace("USDT", "/USDT"),
                            "market": "crypto",
                            "timeframe": timeframe,
                            "timestamp": int(k["t"] / 1000),
                            "open": float(k["o"]),
                            "high": float(k["h"]),
                            "low": float(k["l"]),
                            "close": float(k["c"]),
                            "volume": float(k["v"]),
                        })
                        key = f"{symbol}_{timeframe}"
                        if key not in candle_store:
                            candle_store[key] = []
                        candle_store[key].append(candle)
                        candle_store[key] = candle_store[key][-500:]  # keep last 500
                        if on_candle:
                            await on_candle(candle)
        except Exception as e:
            print(f"[Binance] Stream error {symbol}: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

def get_candles(symbol: str, timeframe: str, limit: int = 200) -> list:
    """Get candles from in-memory store."""
    key = f"{symbol}_{timeframe}"
    candles = candle_store.get(key, [])
    return candles[-limit:]
```

---

## Step 2 — OANDA connector

### backend/connectors/oanda.py
```python
"""
BLARE OANDA Connector
Fetches live and historical OHLCV data for forex pairs.
Uses OANDA v20 REST API with streaming support.
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from config.settings import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_ENVIRONMENT
from connectors.unified import normalize_candle

BASE_URL = (
    "https://api-fxpractice.oanda.com"
    if OANDA_ENVIRONMENT == "practice"
    else "https://api-fxtrade.oanda.com"
)

HEADERS = {
    "Authorization": f"Bearer {OANDA_API_KEY}",
    "Content-Type": "application/json"
}

TIMEFRAME_MAP = {
    "1m": "M1", "5m": "M5", "15m": "M15",
    "1h": "H1", "4h": "H4", "1d": "D"
}

candle_store = {}

async def fetch_historical(symbol: str, timeframe: str, limit: int = 200) -> list:
    """Fetch historical OHLCV from OANDA REST API."""
    try:
        instrument = symbol.replace("/", "_")
        url = f"{BASE_URL}/v3/instruments/{instrument}/candles"
        params = {
            "granularity": TIMEFRAME_MAP[timeframe],
            "count": limit,
            "price": "M"  # midpoint
        }
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=HEADERS, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            candles = []
            for c in data.get("candles", []):
                if not c.get("complete"):
                    continue
                mid = c["mid"]
                candle = normalize_candle({
                    "symbol": symbol,
                    "market": "forex",
                    "timeframe": timeframe,
                    "timestamp": int(datetime.fromisoformat(
                        c["time"].replace("Z", "+00:00")).timestamp()),
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": float(c.get("volume", 0)),
                })
                candles.append(candle)
            key = f"{symbol}_{timeframe}"
            candle_store[key] = candles
            print(f"[OANDA] Loaded {len(candles)} candles for {symbol} {timeframe}")
            return candles
    except Exception as e:
        print(f"[OANDA] fetch_historical error {symbol}: {e}")
        return []

async def poll_candles(symbol: str, timeframe: str, on_candle=None, interval: int = 60):
    """Poll OANDA for new candles on a schedule."""
    print(f"[OANDA] Starting poll: {symbol} {timeframe} every {interval}s")
    while True:
        try:
            candles = await fetch_historical(symbol, timeframe, limit=2)
            if candles and on_candle:
                await on_candle(candles[-1])
        except Exception as e:
            print(f"[OANDA] Poll error {symbol}: {e}")
        await asyncio.sleep(interval)

def get_candles(symbol: str, timeframe: str, limit: int = 200) -> list:
    """Get candles from in-memory store."""
    key = f"{symbol}_{timeframe}"
    return candle_store.get(key, [])[-limit:]
```

---

## Step 3 — Alpha Vantage connector

### backend/connectors/alphavantage.py
```python
"""
BLARE Alpha Vantage Connector
Fetches OHLCV data for indices and commodities.
Uses polling — Alpha Vantage does not support WebSocket.
"""
import httpx
import asyncio
from datetime import datetime
from config.settings import ALPHA_VANTAGE_API_KEY
from connectors.unified import normalize_candle

BASE_URL = "https://www.alphavantage.co/query"

TIMEFRAME_MAP = {
    "1m": "1min", "5m": "5min", "15m": "15min",
    "1h": "60min", "4h": "60min",  # AV max is 60min intraday
    "1d": "daily"
}

# Market type per symbol
SYMBOL_MARKET = {
    "SPX": "indices", "NDX": "indices", "DAX": "indices",
    "XAU": "commodities", "WTI": "commodities", "XAG": "commodities"
}

candle_store = {}

async def fetch_historical(symbol: str, timeframe: str, limit: int = 200) -> list:
    """Fetch historical OHLCV from Alpha Vantage."""
    try:
        tf = TIMEFRAME_MAP.get(timeframe, "60min")
        is_daily = tf == "daily"
        function = "TIME_SERIES_DAILY" if is_daily else "TIME_SERIES_INTRADAY"
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY,
            "outputsize": "compact"
        }
        if not is_daily:
            params["interval"] = tf

        async with httpx.AsyncClient() as client:
            res = await client.get(BASE_URL, params=params, timeout=15)
            res.raise_for_status()
            data = res.json()

        series_key = next((k for k in data if "Time Series" in k), None)
        if not series_key:
            print(f"[AlphaVantage] No data for {symbol}: {data.get('Note', data.get('Information', 'Unknown error'))}")
            return []

        series = data[series_key]
        market = SYMBOL_MARKET.get(symbol, "indices")
        candles = []
        for ts, values in list(series.items())[:limit]:
            dt = datetime.fromisoformat(ts)
            candle = normalize_candle({
                "symbol": symbol,
                "market": market,
                "timeframe": timeframe,
                "timestamp": int(dt.timestamp()),
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": float(values.get("5. volume", 0)),
            })
            candles.append(candle)

        candles.reverse()  # oldest first
        key = f"{symbol}_{timeframe}"
        candle_store[key] = candles
        print(f"[AlphaVantage] Loaded {len(candles)} candles for {symbol} {timeframe}")
        return candles
    except Exception as e:
        print(f"[AlphaVantage] fetch_historical error {symbol}: {e}")
        return []

async def poll_candles(symbol: str, timeframe: str, on_candle=None, interval: int = 60):
    """Poll Alpha Vantage for new candles. Respects rate limits."""
    print(f"[AlphaVantage] Starting poll: {symbol} {timeframe} every {interval}s")
    while True:
        try:
            candles = await fetch_historical(symbol, timeframe, limit=5)
            if candles and on_candle:
                await on_candle(candles[-1])
        except Exception as e:
            print(f"[AlphaVantage] Poll error {symbol}: {e}")
        await asyncio.sleep(interval)

def get_candles(symbol: str, timeframe: str, limit: int = 200) -> list:
    """Get candles from in-memory store."""
    key = f"{symbol}_{timeframe}"
    return candle_store.get(key, [])[-limit:]
```

---

## Step 4 — Unified normalizer

### backend/connectors/unified.py
```python
"""
BLARE Unified Data Normalizer
Converts any connector's raw candle dict into the standard BLARE OHLCV format.
All engine code above this layer only ever sees this format.
"""
from typing import Optional

def normalize_candle(raw: dict) -> dict:
    """
    Normalize any raw candle dict into standard BLARE OHLCV format.
    Returns a clean, typed candle object.
    """
    return {
        "symbol":    str(raw["symbol"]),
        "market":    str(raw["market"]),     # crypto|forex|indices|commodities
        "timeframe": str(raw["timeframe"]),  # 1m|5m|15m|1h|4h|1d
        "timestamp": int(raw["timestamp"]),  # unix seconds
        "open":      float(raw["open"]),
        "high":      float(raw["high"]),
        "low":       float(raw["low"]),
        "close":     float(raw["close"]),
        "volume":    float(raw.get("volume", 0)),
    }

def get_all_candles() -> dict:
    """
    Returns merged candle store from all connectors.
    Key format: "SYMBOL_timeframe"
    """
    from connectors import binance, oanda, alphavantage
    return {
        **binance.candle_store,
        **oanda.candle_store,
        **alphavantage.candle_store,
    }

def get_candles(symbol: str, timeframe: str, limit: int = 200) -> list:
    """
    Fetch candles for any symbol from the correct connector automatically.
    """
    from config.settings import CRYPTO_SYMBOLS, FOREX_SYMBOLS, INDICES_SYMBOLS, COMMODITY_SYMBOLS
    from connectors import binance, oanda, alphavantage

    clean = symbol.replace("/", "").replace("_", "")
    if any(clean in s.replace("/", "").replace("_", "") for s in CRYPTO_SYMBOLS):
        return binance.get_candles(symbol.replace("/", "").replace("_", ""), timeframe, limit)
    elif any(symbol.replace("/", "_") in s or symbol in s for s in FOREX_SYMBOLS):
        return oanda.get_candles(symbol, timeframe, limit)
    else:
        return alphavantage.get_candles(symbol, timeframe, limit)
```

---

## Step 5 — Scanner loop (APScheduler)

### backend/engine/scanner.py
```python
"""
BLARE Scanner
Runs the pattern detection loop on a schedule.
Loads all strategy rules and checks them against live candle data.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from connectors.unified import get_candles
from config.settings import (
    CRYPTO_SYMBOLS, FOREX_SYMBOLS,
    INDICES_SYMBOLS, COMMODITY_SYMBOLS
)
import asyncio

scheduler = AsyncIOScheduler()

ALL_INSTRUMENTS = [
    {"symbol": s.replace("USDT", "/USDT"), "market": "crypto"} for s in CRYPTO_SYMBOLS
] + [
    {"symbol": s.replace("_", "/"), "market": "forex"} for s in FOREX_SYMBOLS
] + [
    {"symbol": s, "market": "indices"} for s in INDICES_SYMBOLS
] + [
    {"symbol": s, "market": "commodities"} for s in COMMODITY_SYMBOLS
]

SCAN_TIMEFRAMES = ["15m", "1h", "4h"]

async def scan_all():
    """Main scan loop — runs every 30s."""
    print("[Scanner] Running scan...")
    for instrument in ALL_INSTRUMENTS:
        for tf in SCAN_TIMEFRAMES:
            candles = get_candles(instrument["symbol"], tf, limit=200)
            if len(candles) < 50:
                continue
            # Pattern engine hooks in here in Session 03
            # For now just log data is flowing
    print(f"[Scanner] Scan complete — {len(ALL_INSTRUMENTS)} instruments x {len(SCAN_TIMEFRAMES)} timeframes")

def start_scanner():
    """Initialize and start the APScheduler scan loop."""
    scheduler.add_job(scan_all, "interval", seconds=30, id="main_scan")
    scheduler.start()
    print("[Scanner] Scheduler started — scanning every 30s")
```

---

## Step 6 — Preload historical data on startup

Update `backend/main.py` startup event:

```python
@app.on_event("startup")
async def startup():
    print(f"[BLARE] Starting in {APP_ENV} mode")
    init_firebase()

    # Preload historical candles
    from connectors import binance, oanda, alphavantage
    from config.settings import CRYPTO_SYMBOLS, FOREX_SYMBOLS, INDICES_SYMBOLS, COMMODITY_SYMBOLS

    print("[BLARE] Preloading historical data...")

    # Crypto — all timeframes
    for symbol in CRYPTO_SYMBOLS:
        for tf in ["15m", "1h", "4h", "1d"]:
            await binance.fetch_historical(symbol, tf, limit=200)
            await asyncio.sleep(0.2)

    # Forex
    for symbol in FOREX_SYMBOLS:
        for tf in ["15m", "1h", "4h"]:
            await oanda.fetch_historical(symbol.replace("_", "/"), tf, limit=200)
            await asyncio.sleep(0.5)

    # Indices + Commodities (respect AV rate limit — 5 req/min free tier)
    for symbol in INDICES_SYMBOLS + COMMODITY_SYMBOLS:
        await alphavantage.fetch_historical(symbol, "1h", limit=100)
        await asyncio.sleep(15)  # AV rate limit buffer

    # Start WebSocket streams
    import asyncio
    for symbol in CRYPTO_SYMBOLS:
        for tf in ["15m", "1h", "4h"]:
            asyncio.create_task(binance.stream_candles(symbol, tf))

    # Start scanner
    from engine.scanner import start_scanner
    start_scanner()

    print("[BLARE] All systems ready")
```

---

## Step 7 — Candles route

### backend/routes/candles.py
```python
"""BLARE candles route — returns OHLCV data for any instrument."""
from fastapi import APIRouter, Query
from connectors.unified import get_candles

router = APIRouter()

@router.get("/{symbol}")
async def get_symbol_candles(
    symbol: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=200, le=500)
):
    """
    Get OHLCV candles for any symbol.
    Symbol examples: BTC-USDT, EUR-USD, SPX, XAU
    Replace / with - in URL: BTC/USDT → BTC-USDT
    """
    clean_symbol = symbol.replace("-", "/")
    candles = get_candles(clean_symbol, timeframe, limit)
    return {
        "symbol": clean_symbol,
        "timeframe": timeframe,
        "count": len(candles),
        "candles": candles
    }
```

Add to `main.py`:
```python
from routes import candles
app.include_router(candles.router, prefix="/candles", tags=["candles"])
```

---

## Step 8 — Verify everything

Test these endpoints after starting:

```bash
# Health
curl http://localhost:8000/health

# Crypto candles
curl "http://localhost:8000/candles/BTC-USDT?timeframe=1h&limit=10"

# Forex candles
curl "http://localhost:8000/candles/EUR-USD?timeframe=1h&limit=10"

# Indices
curl "http://localhost:8000/candles/SPX?timeframe=1h&limit=10"
```

Expected: each returns JSON with candles array in unified OHLCV format.

Checklist:
- [ ] Binance returns live crypto candles
- [ ] OANDA returns live forex candles
- [ ] Alpha Vantage returns indices + commodities
- [ ] All candles in identical OHLCV format
- [ ] Scanner loop logging every 30s
- [ ] No hardcoded API keys

---

## Session 02 Complete

Commit message: `feat: session 02 — data pipeline complete`

Next: **Session 03 — Pattern Engine Core**
