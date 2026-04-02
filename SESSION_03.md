# BLARE — Session 03: Pattern Engine Core

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to build
Prerequisite: Session 02 complete

---

## Context

This session builds the rule library loader and scanner core.
By the end, the app reads your `.txt` strategy files, runs them
against live candle data, creates Signal objects on match,
and saves them to Firestore.

---

## Goals

- [ ] Strategy loader reads all `.txt` files from `/strategies/`
- [ ] Scanner runs loaded rules against live OHLCV data
- [ ] First strategy live end-to-end
- [ ] Signal object created + saved to Firestore on match
- [ ] GET /strategies endpoint listing all loaded strategies
- [ ] GET /signals endpoint returning recent signals

---

## Step 1 — Signal model

### backend/models/signal.py
```python
"""
BLARE Signal Model
Standard format for every trading signal BLARE generates.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Signal:
    symbol: str
    market: str           # crypto|forex|indices|commodities
    direction: str        # long|short
    timeframe: str
    pattern: str          # matches strategy .txt filename
    entry: float
    stop: float
    target: float
    rr: float
    confidence: int = 0          # 0-100, filled by AI layer
    ai_note: str = ""            # filled by AI layer
    position_size_pct: float = 1.0
    status: str = "pending"      # pending|approved|rejected|executed
    id: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.rr = round(
            abs(self.target - self.entry) / abs(self.entry - self.stop), 2
        ) if self.entry != self.stop else 0

    def to_dict(self) -> dict:
        return asdict(self)
```

---

## Step 2 — Strategy loader

### backend/engine/loader.py
```python
"""
BLARE Strategy Loader
Reads all .txt strategy files from /strategies/ directory.
Parses them into structured dicts the pattern engine can use.
Adding a new strategy = drop a .txt file + restart. No code changes.
"""
import os
from pathlib import Path
from typing import Dict, List

STRATEGIES_DIR = Path(__file__).parent.parent.parent / "strategies"

_loaded_strategies: Dict[str, dict] = {}

def parse_strategy_file(filepath: Path) -> dict:
    """Parse a BLARE strategy .txt file into a structured dict."""
    strategy = {
        "id": filepath.stem,
        "filepath": str(filepath),
        "raw": {}
    }
    current_key = None
    current_value = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()

            # Skip comments and empty lines
            if line.startswith("#") or not line.strip():
                continue

            # Key: Value on same line
            if ":" in line and not line.startswith(" "):
                if current_key:
                    strategy["raw"][current_key] = "\n".join(current_value).strip()
                parts = line.split(":", 1)
                current_key = parts[0].strip()
                current_value = [parts[1].strip()] if len(parts) > 1 else []
            else:
                if current_key:
                    current_value.append(line.strip())

    if current_key:
        strategy["raw"][current_key] = "\n".join(current_value).strip()

    # Extract key fields
    raw = strategy["raw"]
    strategy.update({
        "name": raw.get("STRATEGY_NAME", strategy["id"]),
        "market": [m.strip() for m in raw.get("MARKET", "all").split(",")],
        "direction": raw.get("DIRECTION", "both"),
        "htf": raw.get("HTF", "1d"),
        "mtf": raw.get("MTF", "4h"),
        "ltf": raw.get("LTF", "15m"),
        "concept": raw.get("CONCEPT", ""),
        "conditions": [v for k, v in raw.items() if k.startswith("CONDITION_") and v],
        "entry_trigger": raw.get("ENTRY_TRIGGER", ""),
        "stop_placement": raw.get("STOP_PLACEMENT", ""),
        "invalidations": [v for k, v in raw.items() if k.startswith("INVALIDATION_") and v],
        "detect_steps": [v for k, v in raw.items() if k.startswith("DETECT_STEP_") and v],
        "min_rr": float(raw.get("MINIMUM_RR", "2.0")),
    })
    return strategy

def load_all_strategies() -> Dict[str, dict]:
    """Load all strategy .txt files from the strategies directory."""
    global _loaded_strategies
    _loaded_strategies = {}

    if not STRATEGIES_DIR.exists():
        print(f"[Loader] Strategies directory not found: {STRATEGIES_DIR}")
        return {}

    files = list(STRATEGIES_DIR.glob("*.txt"))
    files = [f for f in files if not f.name.startswith("_")]  # skip _template

    for filepath in files:
        try:
            strategy = parse_strategy_file(filepath)
            _loaded_strategies[strategy["id"]] = strategy
            print(f"[Loader] Loaded strategy: {strategy['id']}")
        except Exception as e:
            print(f"[Loader] Error loading {filepath.name}: {e}")

    print(f"[Loader] Total strategies loaded: {len(_loaded_strategies)}")
    return _loaded_strategies

def get_strategies() -> Dict[str, dict]:
    """Return all currently loaded strategies."""
    return _loaded_strategies

def get_strategy(strategy_id: str) -> dict:
    """Return a single strategy by ID."""
    return _loaded_strategies.get(strategy_id)
```

---

## Step 3 — Core scanner with Firestore saving

### backend/engine/scanner.py (full version)
```python
"""
BLARE Scanner
Main scan loop — runs all loaded strategies against live candle data.
Creates Signal objects on pattern match and saves to Firestore.
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from connectors.unified import get_candles
from engine.loader import get_strategies
from engine.patterns.smc import detect_all as detect_smc
from models.signal import Signal
from config.firebase import get_db
from config.settings import (
    CRYPTO_SYMBOLS, FOREX_SYMBOLS,
    INDICES_SYMBOLS, COMMODITY_SYMBOLS
)

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

# Track recently fired signals to avoid duplicates
_recent_signals: dict = {}  # "SYMBOL_pattern_direction" → timestamp

async def save_signal(signal: Signal):
    """Save a signal to Firestore."""
    try:
        db = get_db()
        db.collection("signals").document(signal.id).set(signal.to_dict())
        print(f"[Scanner] Signal saved: {signal.symbol} {signal.direction.upper()} "
              f"{signal.pattern} confidence:{signal.confidence}")
    except Exception as e:
        print(f"[Scanner] Error saving signal: {e}")

async def scan_instrument(symbol: str, market: str, timeframe: str, strategies: dict):
    """Scan a single instrument on a single timeframe against all strategies."""
    candles = get_candles(symbol, timeframe, limit=200)
    if len(candles) < 50:
        return

    for strategy_id, strategy in strategies.items():
        # Skip if strategy doesn't apply to this market
        if "all" not in strategy["market"] and market not in strategy["market"]:
            continue

        try:
            # Dedup check — don't fire same signal twice within 4h
            dedup_key = f"{symbol}_{strategy_id}"
            import time
            now = time.time()
            if dedup_key in _recent_signals:
                if now - _recent_signals[dedup_key] < 14400:  # 4 hours
                    continue

            # Run pattern detection (SMC stub for now, expands in Sessions 04-05)
            result = detect_smc(candles, strategy, timeframe)

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
                    rr=0,  # auto-calculated in __post_init__
                )

                # Skip if R:R below minimum
                if signal.rr < strategy.get("min_rr", 2.0):
                    continue

                _recent_signals[dedup_key] = now
                await save_signal(signal)

        except Exception as e:
            print(f"[Scanner] Error scanning {symbol} {strategy_id}: {e}")

async def scan_all():
    """Main scan loop — runs every 30s."""
    strategies = get_strategies()
    if not strategies:
        print("[Scanner] No strategies loaded — skipping scan")
        return

    print(f"[Scanner] Scanning {len(ALL_INSTRUMENTS)} instruments x "
          f"{len(SCAN_TIMEFRAMES)} timeframes x {len(strategies)} strategies")

    tasks = []
    for instrument in ALL_INSTRUMENTS:
        for tf in SCAN_TIMEFRAMES:
            tasks.append(scan_instrument(
                instrument["symbol"], instrument["market"], tf, strategies
            ))
    await asyncio.gather(*tasks)
    print("[Scanner] Scan complete")

def start_scanner():
    """Initialize and start the scanner."""
    from engine.loader import load_all_strategies
    load_all_strategies()
    scheduler.add_job(scan_all, "interval", seconds=30, id="main_scan")
    scheduler.start()
    print("[Scanner] Started — scanning every 30s")
```

---

## Step 4 — SMC detection stub

### backend/engine/patterns/smc.py (stub for Session 03, expanded in 04)
```python
"""
BLARE SMC / ICT Pattern Detection
Full implementation in Session 04.
This stub provides the interface so the scanner works end-to-end.
"""
from typing import Optional

def detect_all(candles: list, strategy: dict, timeframe: str) -> Optional[dict]:
    """
    Run all SMC detections for a strategy against candle data.
    Returns a signal dict if pattern found, None otherwise.
    Full implementation in Session 04.
    """
    # Stub: returns None (no signals) until Session 04
    return None

def find_swing_high(candles: list, lookback: int = 20) -> Optional[dict]:
    """Find the most recent swing high."""
    if len(candles) < lookback:
        return None
    window = candles[-lookback:]
    highest = max(window, key=lambda c: c["high"])
    return highest

def find_swing_low(candles: list, lookback: int = 20) -> Optional[dict]:
    """Find the most recent swing low."""
    if len(candles) < lookback:
        return None
    window = candles[-lookback:]
    lowest = min(window, key=lambda c: c["low"])
    return lowest
```

---

## Step 5 — Strategies route

### backend/routes/strategies.py
```python
"""BLARE strategies route."""
from fastapi import APIRouter
from engine.loader import get_strategies

router = APIRouter()

@router.get("/")
async def list_strategies():
    """List all loaded strategies."""
    strategies = get_strategies()
    return {
        "count": len(strategies),
        "strategies": [
            {
                "id": s["id"],
                "name": s["name"],
                "market": s["market"],
                "direction": s["direction"],
                "timeframes": {"htf": s["htf"], "mtf": s["mtf"], "ltf": s["ltf"]},
                "min_rr": s["min_rr"],
                "conditions_count": len(s["conditions"]),
            }
            for s in strategies.values()
        ]
    }

@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get full details of a single strategy."""
    from engine.loader import get_strategy
    strategy = get_strategy(strategy_id)
    if not strategy:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy
```

---

## Step 6 — Signals route

### backend/routes/signals.py
```python
"""BLARE signals route."""
from fastapi import APIRouter, Query
from config.firebase import get_db

router = APIRouter()

@router.get("/")
async def get_signals(limit: int = Query(default=20, le=100)):
    """Get recent signals ordered by creation time."""
    try:
        db = get_db()
        docs = (db.collection("signals")
                  .order_by("created_at", direction="DESCENDING")
                  .limit(limit)
                  .stream())
        signals = [doc.to_dict() for doc in docs]
        return {"count": len(signals), "signals": signals}
    except Exception as e:
        return {"error": str(e), "signals": []}

@router.get("/{signal_id}")
async def get_signal(signal_id: str):
    """Get a single signal by ID."""
    try:
        db = get_db()
        doc = db.collection("signals").document(signal_id).get()
        if not doc.exists:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Signal not found")
        return doc.to_dict()
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{signal_id}/approve")
async def approve_signal(signal_id: str):
    """Approve a pending signal (semi-auto mode)."""
    try:
        db = get_db()
        db.collection("signals").document(signal_id).update({"status": "approved"})
        return {"status": "approved", "signal_id": signal_id}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{signal_id}/reject")
async def reject_signal(signal_id: str):
    """Reject a pending signal (semi-auto mode)."""
    try:
        db = get_db()
        db.collection("signals").document(signal_id).update({"status": "rejected"})
        return {"status": "rejected", "signal_id": signal_id}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Step 7 — First real strategy file

Create `strategies/smc_fvg_entry.txt`:
```
STRATEGY_NAME: SMC Fair Value Gap Entry
STRATEGY_ID: smc_fvg_entry
VERSION: 1.0
AUTHOR: Ovi
SOURCE: Template — expand after YouTube research
MARKET: crypto, forex
DIRECTION: both

HTF: 1d
MTF: 4h
LTF: 15m

CONCEPT:
Smart money leaves Fair Value Gaps (imbalances) when they enter
positions aggressively. Price tends to return to fill these gaps
before continuing in the original direction. We enter when price
returns to an unfilled FVG aligned with HTF bias.

CONDITION_1: HTF (1D) trend is clear — strong directional move in last 5 candles
CONDITION_2: MTF (4H) shows a Fair Value Gap — 3-candle pattern with a gap
CONDITION_3: FVG is unfilled — price has not returned to the gap zone yet
CONDITION_4: Current price is approaching the FVG from the correct direction

ENTRY_TRIGGER:
Price enters the FVG zone on LTF (15m).
Wait for a 15m candle to close in the direction of the HTF trend inside the FVG.
Enter on the next candle open.

ENTRY_TYPE: limit

STOP_PLACEMENT:
Below the lowest point of the FVG zone for longs.
Above the highest point of the FVG zone for shorts.
Add 0.1% buffer.

STOP_TYPE: structure_based

TARGET_1: 50% of position at 1:1 R:R
TARGET_2: Remainder at next structure level / liquidity

TARGET_TYPE: structure_level
MINIMUM_RR: 2.0

INVALIDATION_1: Price closes a full candle through the FVG without reaction
INVALIDATION_2: HTF trend breaks — daily closes opposite direction
INVALIDATION_3: FVG is more than 48 hours old (stale)

AVOID_1: High impact news within 30 minutes
AVOID_2: Price in clear consolidation range on HTF
AVOID_3: Multiple overlapping FVGs — too complex

DETECT_STEP_1: Get last 50 candles on MTF (4H)
DETECT_STEP_2: Scan for FVG — find 3-candle pattern where candle[i].low > candle[i-2].high (bullish FVG) or candle[i].high < candle[i-2].low (bearish FVG)
DETECT_STEP_3: Check FVG is unfilled — no subsequent candle has traded through the gap zone
DETECT_STEP_4: Check current price is within 0.5% of entering the FVG zone
DETECT_STEP_5: Confirm HTF trend direction matches FVG direction

NOTES:
Start with this as the first live strategy.
Expand with more YouTube-sourced strategies as library grows.
```

---

## Step 8 — Verify everything

```bash
# Start backend
cd backend && uvicorn main:app --reload

# Check strategies loaded
curl http://localhost:8000/strategies/
# Should return smc_fvg_entry

# Check signals (empty initially)
curl http://localhost:8000/signals/
```

Checklist:
- [ ] GET /strategies returns loaded .txt files
- [ ] Scanner logs "Scanning X instruments" every 30s
- [ ] No errors in startup logs
- [ ] Firestore console shows signals collection (even if empty)
- [ ] Approve/reject endpoints return 200

---

## Session 03 Complete

Commit message: `feat: session 03 — pattern engine core complete`

Next: **Session 04 — SMC / ICT Detection**
