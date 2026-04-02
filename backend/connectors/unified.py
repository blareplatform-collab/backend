"""
BLARE Unified Data Normalizer
Converts any connector's raw candle dict into the standard BLARE OHLCV format.
All engine code above this layer only ever sees this format.
"""


def normalize_candle(raw: dict) -> dict:
    return {
        "symbol":    str(raw["symbol"]),
        "market":    str(raw["market"]),
        "timeframe": str(raw["timeframe"]),
        "timestamp": int(raw["timestamp"]),
        "open":      float(raw["open"]),
        "high":      float(raw["high"]),
        "low":       float(raw["low"]),
        "close":     float(raw["close"]),
        "volume":    float(raw.get("volume", 0)),
    }


def get_all_candles() -> dict:
    from connectors import binance, oanda, alphavantage
    return {
        **binance.candle_store,
        **oanda.candle_store,
        **alphavantage.candle_store,
    }


def get_candles(symbol: str, timeframe: str, limit: int = 200) -> list:
    from config.settings import CRYPTO_SYMBOLS, FOREX_SYMBOLS
    from connectors import binance, oanda, alphavantage

    clean = symbol.replace("/", "").replace("_", "")
    if any(clean in s.replace("/", "").replace("_", "") for s in CRYPTO_SYMBOLS):
        return binance.get_candles(symbol.replace("/", "").replace("_", ""), timeframe, limit)
    elif any(symbol.replace("/", "_") in s or symbol in s for s in FOREX_SYMBOLS):
        return oanda.get_candles(symbol, timeframe, limit)
    else:
        return alphavantage.get_candles(symbol, timeframe, limit)
