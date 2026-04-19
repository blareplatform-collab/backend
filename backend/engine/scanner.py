"""
BLARE Scanner
Main scan loop — runs all loaded strategies against live candle data.
Creates Signal objects on pattern match and saves to Firestore.
"""
import asyncio
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from connectors.unified import get_candles
from engine.loader import get_strategies
from engine.patterns.smc import detect_all as detect_smc
from engine.patterns.wyckoff import detect_wyckoff
from engine.patterns.classic_ta import detect_all as detect_classic
from models.signal import Signal
from ai.validator import validate_and_enrich
from config.firebase import get_db
from config.settings import CRYPTO_SYMBOLS, AUTO_TRADE_MODE
from notifications.fcm import send_signal_notification
from execution.router import execute_signal

scheduler = AsyncIOScheduler()

ALL_INSTRUMENTS = [
    {"symbol": s.replace("USDT", "/USDT"), "market": "crypto"} for s in CRYPTO_SYMBOLS
]

SCAN_TIMEFRAMES = ["15m", "1h", "4h"]

_recent_signals: dict = {}


async def save_signal(signal: Signal):
    try:
        db = get_db()
        db.collection("signals").document(signal.id).set(signal.to_dict())
        print(f"[Scanner] Signal saved: {signal.symbol} {signal.direction.upper()} "
              f"{signal.pattern} confidence:{signal.confidence}")
    except Exception as e:
        print(f"[Scanner] Error saving signal: {e}")


async def scan_instrument(symbol: str, market: str, timeframe: str, strategies: dict):
    candles = get_candles(symbol, timeframe, limit=200)
    if len(candles) < 50:
        return

    for strategy_id, strategy in strategies.items():
        if "all" not in strategy["market"] and market not in strategy["market"]:
            continue
        try:
            dedup_key = f"{symbol}_{strategy_id}"
            now = time.time()
            if dedup_key in _recent_signals:
                if now - _recent_signals[dedup_key] < 14400:
                    continue

            result = None
            for detector in [
                lambda c, s: detect_smc(c, s, timeframe),
                lambda c, s: detect_wyckoff(c, s),
                lambda c, s: detect_classic(c, s),
            ]:
                result = detector(candles, strategy)
                if result:
                    break

            if result:
                signal = Signal(
                    symbol=symbol,
                    market=market,
                    direction=result["direction"],
                    timeframe=timeframe,
                    pattern=strategy_id,
                    entry=result["entry"],
                    stop=result["stop"],
                    target=result["target"],
                )
                if signal.rr < strategy.get("min_rr", 2.0):
                    continue
                enriched = await validate_and_enrich(signal, candles, strategy)
                if enriched:
                    _recent_signals[dedup_key] = now
                    await save_signal(enriched)
                    await send_signal_notification(enriched.to_dict())
                    if AUTO_TRADE_MODE == "auto":
                        await execute_signal(enriched.to_dict())
        except Exception as e:
            print(f"[Scanner] Error scanning {symbol} {strategy_id}: {e}")


async def scan_all():
    strategies = get_strategies()
    if not strategies:
        print("[Scanner] No strategies loaded — skipping scan")
        return

    print(f"[Scanner] Scanning {len(ALL_INSTRUMENTS)} instruments x "
          f"{len(SCAN_TIMEFRAMES)} timeframes x {len(strategies)} strategies")

    tasks = [
        scan_instrument(inst["symbol"], inst["market"], tf, strategies)
        for inst in ALL_INSTRUMENTS
        for tf in SCAN_TIMEFRAMES
    ]
    await asyncio.gather(*tasks)
    print("[Scanner] Scan complete")


def start_scanner():
    from engine.loader import load_all_strategies
    load_all_strategies()
    scheduler.add_job(scan_all, "interval", seconds=30, id="main_scan")
    scheduler.start()
    print("[Scanner] Started — scanning every 30s")
