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
    "1h": "60min", "4h": "60min",
    "1d": "daily"
}

SYMBOL_MARKET = {
    "SPX": "indices", "NDX": "indices", "DAX": "indices",
    "XAU": "commodities", "WTI": "commodities", "XAG": "commodities"
}

candle_store = {}


async def fetch_historical(symbol: str, timeframe: str, limit: int = 200) -> list:
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
            candle = normalize_candle({
                "symbol": symbol,
                "market": market,
                "timeframe": timeframe,
                "timestamp": int(datetime.fromisoformat(ts).timestamp()),
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": float(values.get("5. volume", 0)),
            })
            candles.append(candle)

        candles.reverse()
        key = f"{symbol}_{timeframe}"
        candle_store[key] = candles
        print(f"[AlphaVantage] Loaded {len(candles)} candles for {symbol} {timeframe}")
        return candles
    except Exception as e:
        print(f"[AlphaVantage] fetch_historical error {symbol}: {e}")
        return []


async def poll_candles(symbol: str, timeframe: str, on_candle=None, interval: int = 60):
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
    key = f"{symbol}_{timeframe}"
    return candle_store.get(key, [])[-limit:]
