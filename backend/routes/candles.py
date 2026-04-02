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
