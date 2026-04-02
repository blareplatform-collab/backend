"""
BLARE OANDA Connector
Fetches live and historical OHLCV data for forex pairs.
Uses OANDA v20 REST API with streaming support.
"""
import httpx
import asyncio
from datetime import datetime
from config.settings import OANDA_API_KEY, OANDA_ENVIRONMENT
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
    try:
        instrument = symbol.replace("/", "_")
        url = f"{BASE_URL}/v3/instruments/{instrument}/candles"
        params = {"granularity": TIMEFRAME_MAP[timeframe], "count": limit, "price": "M"}
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
    key = f"{symbol}_{timeframe}"
    return candle_store.get(key, [])[-limit:]
