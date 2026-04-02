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

# Always use mainnet for market data — testnet has no real price history
BASE_URL = "https://api.binance.com"
WS_BASE = "wss://stream.binance.com:9443/ws"
# Testnet only used for order execution
EXEC_URL = "https://testnet.binance.vision" if BINANCE_TESTNET else "https://api.binance.com"

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
    """Get candles from in-memory store, fetching if empty."""
    key = f"{symbol}_{timeframe}"
    candles = candle_store.get(key, [])
    if not candles:
        # Fetch on-demand synchronously as fallback
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, fetch_historical(symbol, timeframe, limit))
                    candles = future.result(timeout=15)
            else:
                candles = loop.run_until_complete(fetch_historical(symbol, timeframe, limit))
        except Exception as e:
            print(f"[Binance] on-demand fetch error: {e}")
    return candles[-limit:]
