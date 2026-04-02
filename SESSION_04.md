# BLARE — Session 04: SMC / ICT Detection

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to build
Prerequisite: Session 03 complete

---

## Context

This session builds the full SMC / ICT pattern detection library.
Every function takes a candles array and returns a detected pattern or None.
By the end, BLARE can detect the core Smart Money concepts used by
ICT traders — the patterns most commonly taught on YouTube.

---

## Goals

- [ ] Break of Structure (BOS) detection
- [ ] Change of Character (CHoCH) detection
- [ ] Fair Value Gap (FVG) — bullish + bearish
- [ ] Order Blocks (OB) — bullish + bearish
- [ ] Liquidity sweeps — highs + lows
- [ ] Premium / Discount zones
- [ ] Scanner integrated with all detectors
- [ ] At least 3 SMC strategy .txt files live

---

## Step 1 — Full SMC detection library

### backend/engine/patterns/smc.py
```python
"""
BLARE SMC / ICT Pattern Detection Library
Implements the core Smart Money Concepts used in ICT methodology.

Detection functions:
  - find_swing_high / find_swing_low
  - detect_bos (Break of Structure)
  - detect_choch (Change of Character)
  - detect_fvg (Fair Value Gap)
  - detect_order_block (Order Block)
  - detect_liquidity_sweep
  - get_premium_discount_zone
  - detect_all (main entry point called by scanner)
"""
from typing import Optional, List

# ─────────────────────────────────────────────
# SWING STRUCTURE
# ─────────────────────────────────────────────

def find_swing_highs(candles: list, lookback: int = 5) -> list:
    """
    Find all swing highs in candle data.
    A swing high = candle whose high is higher than the N candles
    on each side.
    """
    highs = []
    for i in range(lookback, len(candles) - lookback):
        window_highs = [c["high"] for c in candles[i-lookback:i+lookback+1]]
        if candles[i]["high"] == max(window_highs):
            highs.append({"index": i, "price": candles[i]["high"],
                          "candle": candles[i]})
    return highs

def find_swing_lows(candles: list, lookback: int = 5) -> list:
    """
    Find all swing lows in candle data.
    A swing low = candle whose low is lower than the N candles on each side.
    """
    lows = []
    for i in range(lookback, len(candles) - lookback):
        window_lows = [c["low"] for c in candles[i-lookback:i+lookback+1]]
        if candles[i]["low"] == min(window_lows):
            lows.append({"index": i, "price": candles[i]["low"],
                         "candle": candles[i]})
    return lows

# ─────────────────────────────────────────────
# BREAK OF STRUCTURE (BOS)
# ─────────────────────────────────────────────

def detect_bos(candles: list, lookback: int = 20) -> Optional[dict]:
    """
    Detect Break of Structure (BOS).

    Bullish BOS: price closes above a previous swing high — continuation up.
    Bearish BOS: price closes below a previous swing low — continuation down.

    Returns dict with direction, level, and candle index or None.
    """
    if len(candles) < lookback + 5:
        return None

    recent = candles[-lookback:]
    current = candles[-1]

    swing_highs = find_swing_highs(recent[:-3], lookback=3)
    swing_lows = find_swing_lows(recent[:-3], lookback=3)

    if swing_highs:
        last_high = swing_highs[-1]["price"]
        if current["close"] > last_high:
            return {
                "type": "BOS",
                "direction": "bullish",
                "level": last_high,
                "candle": current,
                "description": f"BOS: closed above swing high {last_high:.5f}"
            }

    if swing_lows:
        last_low = swing_lows[-1]["price"]
        if current["close"] < last_low:
            return {
                "type": "BOS",
                "direction": "bearish",
                "level": last_low,
                "candle": current,
                "description": f"BOS: closed below swing low {last_low:.5f}"
            }
    return None

# ─────────────────────────────────────────────
# CHANGE OF CHARACTER (CHoCH)
# ─────────────────────────────────────────────

def detect_choch(candles: list, lookback: int = 30) -> Optional[dict]:
    """
    Detect Change of Character (CHoCH).

    CHoCH = the FIRST break of structure against the prevailing trend.
    Indicates potential trend reversal (vs BOS which is continuation).

    Bullish CHoCH: in a downtrend, price closes above a previous swing high.
    Bearish CHoCH: in an uptrend, price closes below a previous swing low.
    """
    if len(candles) < lookback + 5:
        return None

    recent = candles[-lookback:]

    # Determine prevailing trend from first half of lookback
    midpoint = len(recent) // 2
    first_half = recent[:midpoint]
    second_half = recent[midpoint:]

    first_avg = sum(c["close"] for c in first_half) / len(first_half)
    second_avg = sum(c["close"] for c in second_half) / len(second_half)

    current = candles[-1]
    swing_highs = find_swing_highs(recent[:-3], lookback=3)
    swing_lows = find_swing_lows(recent[:-3], lookback=3)

    # Bearish trend → look for bullish CHoCH
    if second_avg < first_avg and swing_highs:
        last_high = swing_highs[-1]["price"]
        if current["close"] > last_high:
            return {
                "type": "CHoCH",
                "direction": "bullish",
                "level": last_high,
                "candle": current,
                "description": f"CHoCH: bullish reversal signal above {last_high:.5f}"
            }

    # Bullish trend → look for bearish CHoCH
    if second_avg > first_avg and swing_lows:
        last_low = swing_lows[-1]["price"]
        if current["close"] < last_low:
            return {
                "type": "CHoCH",
                "direction": "bearish",
                "level": last_low,
                "candle": current,
                "description": f"CHoCH: bearish reversal signal below {last_low:.5f}"
            }
    return None

# ─────────────────────────────────────────────
# FAIR VALUE GAP (FVG)
# ─────────────────────────────────────────────

def detect_fvg(candles: list, min_gap_pct: float = 0.05) -> List[dict]:
    """
    Detect all Fair Value Gaps in candle data.

    FVG = 3-candle pattern where the first and third candle
    don't overlap — leaving a price gap (imbalance).

    Bullish FVG: candle[i].low > candle[i-2].high
    Bearish FVG: candle[i].high < candle[i-2].low

    Only returns unfilled FVGs (price hasn't traded back through).
    Returns list of FVG dicts ordered newest first.
    """
    fvgs = []
    if len(candles) < 3:
        return fvgs

    for i in range(2, len(candles)):
        c1 = candles[i - 2]
        c3 = candles[i]

        # Bullish FVG
        if c3["low"] > c1["high"]:
            gap_size = (c3["low"] - c1["high"]) / c1["high"] * 100
            if gap_size >= min_gap_pct:
                # Check if still unfilled
                filled = any(
                    c["low"] <= c3["low"] and c["high"] >= c1["high"]
                    for c in candles[i+1:]
                )
                if not filled:
                    fvgs.append({
                        "type": "FVG",
                        "direction": "bullish",
                        "upper": c3["low"],
                        "lower": c1["high"],
                        "midpoint": (c3["low"] + c1["high"]) / 2,
                        "gap_pct": round(gap_size, 3),
                        "index": i,
                        "candle": candles[i],
                        "filled": False,
                        "description": f"Bullish FVG {c1['high']:.5f} - {c3['low']:.5f}"
                    })

        # Bearish FVG
        if c3["high"] < c1["low"]:
            gap_size = (c1["low"] - c3["high"]) / c1["low"] * 100
            if gap_size >= min_gap_pct:
                filled = any(
                    c["high"] >= c3["high"] and c["low"] <= c1["low"]
                    for c in candles[i+1:]
                )
                if not filled:
                    fvgs.append({
                        "type": "FVG",
                        "direction": "bearish",
                        "upper": c1["low"],
                        "lower": c3["high"],
                        "midpoint": (c1["low"] + c3["high"]) / 2,
                        "gap_pct": round(gap_size, 3),
                        "index": i,
                        "candle": candles[i],
                        "filled": False,
                        "description": f"Bearish FVG {c3['high']:.5f} - {c1['low']:.5f}"
                    })

    return sorted(fvgs, key=lambda x: x["index"], reverse=True)

# ─────────────────────────────────────────────
# ORDER BLOCKS (OB)
# ─────────────────────────────────────────────

def detect_order_block(candles: list, lookback: int = 50) -> List[dict]:
    """
    Detect Order Blocks (OB).

    An Order Block is the last opposing candle before a strong
    impulsive move. It represents an area where institutional
    orders were placed.

    Bullish OB: last bearish candle before a strong bullish move.
    Bearish OB: last bullish candle before a strong bearish move.

    Strong move = candle body >= 2x average body size in window.
    """
    obs = []
    if len(candles) < lookback:
        return obs

    recent = candles[-lookback:]
    avg_body = sum(abs(c["close"] - c["open"]) for c in recent) / len(recent)

    for i in range(1, len(recent) - 1):
        current = recent[i]
        next_c = recent[i + 1]
        body = abs(current["close"] - current["open"])
        next_body = abs(next_c["close"] - next_c["open"])

        # Bullish OB: bearish candle followed by strong bullish
        if (current["close"] < current["open"] and
                next_c["close"] > next_c["open"] and
                next_body >= avg_body * 2):
            obs.append({
                "type": "OB",
                "direction": "bullish",
                "upper": current["open"],  # top of bearish candle body
                "lower": current["close"],  # bottom of bearish candle body
                "index": i,
                "candle": current,
                "description": f"Bullish OB {current['close']:.5f} - {current['open']:.5f}"
            })

        # Bearish OB: bullish candle followed by strong bearish
        if (current["close"] > current["open"] and
                next_c["close"] < next_c["open"] and
                next_body >= avg_body * 2):
            obs.append({
                "type": "OB",
                "direction": "bearish",
                "upper": current["close"],  # top of bullish candle body
                "lower": current["open"],  # bottom of bullish candle body
                "index": i,
                "candle": current,
                "description": f"Bearish OB {current['open']:.5f} - {current['close']:.5f}"
            })

    return sorted(obs, key=lambda x: x["index"], reverse=True)

# ─────────────────────────────────────────────
# LIQUIDITY SWEEPS
# ─────────────────────────────────────────────

def detect_liquidity_sweep(candles: list, lookback: int = 20,
                            buffer_pct: float = 0.1) -> Optional[dict]:
    """
    Detect a liquidity sweep.

    A sweep = price wicks above a previous swing high (or below swing low)
    then CLOSES back inside — indicating stop hunt / liquidity grab.

    Bullish sweep: wick above high, close below high → expect reversal down.
    Bearish sweep: wick below low, close above low → expect reversal up.
    Wait: the CLOSE is key. A close above = BOS, not a sweep.
    """
    if len(candles) < lookback + 3:
        return None

    recent = candles[-lookback - 3:-3]
    current = candles[-1]

    swing_highs = find_swing_highs(recent, lookback=3)
    swing_lows = find_swing_lows(recent, lookback=3)

    if swing_highs:
        last_high = swing_highs[-1]["price"]
        buffer = last_high * (buffer_pct / 100)
        # Wick above but close below
        if current["high"] > last_high + buffer and current["close"] < last_high:
            return {
                "type": "SWEEP",
                "direction": "bearish",  # swept highs = bearish signal
                "swept_level": last_high,
                "sweep_high": current["high"],
                "candle": current,
                "description": f"Liquidity sweep above {last_high:.5f}, "
                               f"closed at {current['close']:.5f}"
            }

    if swing_lows:
        last_low = swing_lows[-1]["price"]
        buffer = last_low * (buffer_pct / 100)
        # Wick below but close above
        if current["low"] < last_low - buffer and current["close"] > last_low:
            return {
                "type": "SWEEP",
                "direction": "bullish",  # swept lows = bullish signal
                "swept_level": last_low,
                "sweep_low": current["low"],
                "candle": current,
                "description": f"Liquidity sweep below {last_low:.5f}, "
                               f"closed at {current['close']:.5f}"
            }
    return None

# ─────────────────────────────────────────────
# PREMIUM / DISCOUNT ZONES
# ─────────────────────────────────────────────

def get_premium_discount_zone(candles: list, lookback: int = 50) -> dict:
    """
    Calculate premium and discount zones for a price range.

    Premium = above 50% of the range (expensive — look for shorts).
    Discount = below 50% of the range (cheap — look for longs).
    Equilibrium = 50% level (fair value).
    """
    if len(candles) < lookback:
        return {}

    recent = candles[-lookback:]
    high = max(c["high"] for c in recent)
    low = min(c["low"] for c in recent)
    eq = (high + low) / 2
    current_close = candles[-1]["close"]

    zone = "premium" if current_close > eq else "discount"
    pct_from_eq = ((current_close - eq) / eq) * 100

    return {
        "high": high,
        "low": low,
        "equilibrium": eq,
        "premium_start": eq,
        "discount_end": eq,
        "current_zone": zone,
        "pct_from_equilibrium": round(pct_from_eq, 2),
        "description": f"Price in {zone} zone, {abs(pct_from_eq):.1f}% from EQ"
    }

# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def detect_all(candles: list, strategy: dict, timeframe: str) -> Optional[dict]:
    """
    Run all SMC detections and return a signal dict if a setup is found.
    Called by scanner for every instrument + strategy combination.
    """
    if len(candles) < 50:
        return None

    direction = strategy.get("direction", "both")

    # Run all detectors
    sweep = detect_liquidity_sweep(candles)
    fvgs = detect_fvg(candles)
    bos = detect_bos(candles)
    choch = detect_choch(candles)
    obs = detect_order_block(candles)
    pd_zone = get_premium_discount_zone(candles)

    current = candles[-1]
    current_price = current["close"]

    # ── Strategy: Liquidity Sweep + FVG Entry ──
    if sweep and fvgs:
        sweep_dir = sweep["direction"]
        if direction == "both" or direction == sweep_dir:
            matching_fvgs = [f for f in fvgs if f["direction"] == sweep_dir]
            if matching_fvgs:
                fvg = matching_fvgs[0]
                if sweep_dir == "bullish":
                    entry = fvg["upper"]
                    stop = sweep["sweep_low"] * 0.999
                    target = current_price + (entry - stop) * 2.5
                    return {
                        "direction": "long",
                        "entry": entry,
                        "stop": stop,
                        "target": target,
                        "pattern_detail": f"{sweep['description']} + {fvg['description']}"
                    }
                else:
                    entry = fvg["lower"]
                    stop = sweep["sweep_high"] * 1.001
                    target = current_price - (stop - entry) * 2.5
                    return {
                        "direction": "short",
                        "entry": entry,
                        "stop": stop,
                        "target": target,
                        "pattern_detail": f"{sweep['description']} + {fvg['description']}"
                    }

    # ── Strategy: CHoCH + Order Block Entry ──
    if choch and obs:
        choch_dir = choch["direction"]
        if direction == "both" or direction == choch_dir:
            matching_obs = [o for o in obs if o["direction"] == choch_dir]
            if matching_obs:
                ob = matching_obs[0]
                if choch_dir == "bullish":
                    entry = ob["upper"]
                    stop = ob["lower"] * 0.999
                    target = entry + (entry - stop) * 2.5
                    return {
                        "direction": "long",
                        "entry": entry,
                        "stop": stop,
                        "target": target,
                        "pattern_detail": f"{choch['description']} + {ob['description']}"
                    }
                else:
                    entry = ob["lower"]
                    stop = ob["upper"] * 1.001
                    target = entry - (stop - entry) * 2.5
                    return {
                        "direction": "short",
                        "entry": entry,
                        "stop": stop,
                        "target": target,
                        "pattern_detail": f"{choch['description']} + {ob['description']}"
                    }

    return None
```

---

## Step 2 — Three SMC strategy files

### strategies/smc_liquidity_sweep.txt
```
STRATEGY_NAME: SMC Liquidity Sweep Reversal
STRATEGY_ID: smc_liquidity_sweep
VERSION: 1.0
AUTHOR: Ovi
MARKET: crypto, forex
DIRECTION: both
HTF: 1d
MTF: 4h
LTF: 15m

CONCEPT:
Smart money hunts stop losses placed above swing highs or below swing lows.
After sweeping liquidity, price reverses sharply. We enter on the reversal
confirmed by a close back inside the range.

CONDITION_1: Clear swing high or low visible on MTF
CONDITION_2: Price wicks beyond the level by at least 0.1%
CONDITION_3: Candle closes back inside the range (close-back confirmed)
CONDITION_4: HTF bias aligns with reversal direction

ENTRY_TRIGGER: Next candle open after the sweep close-back candle
ENTRY_TYPE: market
STOP_PLACEMENT: Beyond the sweep wick with 0.1% buffer
STOP_TYPE: structure_based
TARGET_1: 50% at 1:1
TARGET_2: Previous structure level in reversal direction
MINIMUM_RR: 2.0

INVALIDATION_1: Price continues beyond sweep without closing back
INVALIDATION_2: HTF breaks against trade direction

DETECT_STEP_1: Find swing highs and lows in last 20 candles
DETECT_STEP_2: Check if current candle wick exceeds level by > 0.1%
DETECT_STEP_3: Check if current candle CLOSE is back inside range
DETECT_STEP_4: Confirm HTF direction
```

### strategies/smc_order_block.txt
```
STRATEGY_NAME: SMC Order Block Retest
STRATEGY_ID: smc_order_block
VERSION: 1.0
AUTHOR: Ovi
MARKET: crypto, forex
DIRECTION: both
HTF: 1d
MTF: 4h
LTF: 15m

CONCEPT:
Order blocks are zones where institutional orders were placed before
a strong move. Price often returns to these zones to fill remaining
orders before continuing in the original direction.

CONDITION_1: Strong impulsive move away from a zone (2x average candle size)
CONDITION_2: The last opposing candle before that move is identified as OB
CONDITION_3: Price has retraced back to the OB zone
CONDITION_4: HTF trend direction matches OB direction

ENTRY_TRIGGER: Bullish reaction candle closing inside or above OB for longs. Bearish for shorts.
ENTRY_TYPE: limit
STOP_PLACEMENT: Below OB lower boundary for longs, above upper for shorts
STOP_TYPE: structure_based
TARGET_1: 50% at previous high/low
TARGET_2: Next liquidity pool
MINIMUM_RR: 2.0

INVALIDATION_1: Price closes fully through OB without reaction
INVALIDATION_2: New OB formed invalidating the old one

DETECT_STEP_1: Calculate average body size for last 50 candles
DETECT_STEP_2: Find candles with body >= 2x average (impulsive candles)
DETECT_STEP_3: For each impulsive candle, identify the last opposing candle = OB
DETECT_STEP_4: Check if current price is within OB zone boundaries
DETECT_STEP_5: Confirm HTF alignment
```

### strategies/smc_choch_entry.txt
```
STRATEGY_NAME: SMC Change of Character Entry
STRATEGY_ID: smc_choch_entry
VERSION: 1.0
AUTHOR: Ovi
MARKET: crypto, forex
DIRECTION: both
HTF: 1d
MTF: 4h
LTF: 15m

CONCEPT:
A Change of Character (CHoCH) is the first break of market structure
against the prevailing trend — the earliest signal of a reversal.
Unlike BOS which confirms continuation, CHoCH signals that smart money
may be changing direction.

CONDITION_1: Clear trend established on MTF (at least 3 consecutive BOS in one direction)
CONDITION_2: Price makes a CHoCH — breaks the first swing in the opposite direction
CONDITION_3: Retracement back toward the CHoCH level
CONDITION_4: HTF not strongly opposing the reversal

ENTRY_TRIGGER: Retest of CHoCH level with confirming candle
ENTRY_TYPE: limit
STOP_PLACEMENT: Beyond the swing that created CHoCH
STOP_TYPE: structure_based
TARGET_1: 50% at nearest previous structure
TARGET_2: Full trend target if HTF aligns
MINIMUM_RR: 2.5

INVALIDATION_1: Price continues in the original trend direction (CHoCH fails)
INVALIDATION_2: HTF strongly trending against the CHoCH direction

DETECT_STEP_1: Identify prevailing trend — 3+ consecutive higher highs or lower lows
DETECT_STEP_2: Detect first break of structure against the trend = CHoCH
DETECT_STEP_3: Check if price is retesting the CHoCH level (within 0.3%)
DETECT_STEP_4: Look for confirming candle at the retest
```

---

## Step 3 — Verify

```bash
curl http://localhost:8000/strategies/
# Returns 3 SMC strategies + smc_fvg_entry = 4 total

curl http://localhost:8000/signals/
# May start showing signals if setups exist in live data
```

Checklist:
- [ ] All 6 SMC functions implemented and tested
- [ ] detect_all integrates all patterns correctly
- [ ] 4 strategy .txt files loaded
- [ ] Scanner running without errors
- [ ] Signals appearing in Firestore when setups detected

---

## Session 04 Complete

Commit message: `feat: session 04 — SMC/ICT detection library complete`

Next: **Session 05 — Wyckoff + Classic TA Detection**
