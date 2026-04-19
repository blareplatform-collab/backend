"""
BLARE — FastAPI main entry point.
Initializes all services and mounts all routers.
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.firebase import init_firebase
from config.settings import APP_ENV
from routes import signals, trades, strategies, profiles, backtest, candles, analytics

app = FastAPI(
    title="BLARE API",
    description="Bot-powered Liquidity Analysis & Risk Execution",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    print(f"[BLARE] Starting in {APP_ENV} mode")
    init_firebase()

    from connectors import binance
    from config.settings import CRYPTO_SYMBOLS

    print("[BLARE] Preloading historical data...")

    for symbol in CRYPTO_SYMBOLS:
        for tf in ["15m", "1h", "4h", "1d"]:
            await binance.fetch_historical(symbol, tf, limit=200)
            await asyncio.sleep(0.2)

    for symbol in CRYPTO_SYMBOLS:
        for tf in ["15m", "1h", "4h"]:
            asyncio.create_task(binance.stream_candles(symbol, tf))

    from engine.scanner import start_scanner
    start_scanner()

    print("[BLARE] All systems ready")


@app.get("/health")
async def health():
    return {"status": "ok", "app": "BLARE", "version": "1.0.0"}


app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(trades.router, prefix="/trades", tags=["trades"])
app.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
app.include_router(candles.router, prefix="/candles", tags=["candles"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
