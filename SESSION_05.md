# BLARE — Session 05: Wyckoff + Classic TA Detection

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to build
Prerequisite: Session 04 complete

---

## Context

This session adds Wyckoff phase detection and classic chart pattern
recognition. Together with Session 04, BLARE now covers the three
major pattern families traders use — SMC/ICT, Wyckoff, and classic TA.

---

## Goals

- [ ] Wyckoff accumulation + distribution phase detection
- [ ] Spring + UTAD identification
- [ ] Head and Shoulders (regular + inverse)
- [ ] Double top + Double bottom
- [ ] Triangles (ascending, descending, symmetrical)
- [ ] Wedges (rising + falling)
- [ ] Flags (bull + bear)
- [ ] 3 Wyckoff strategy files
- [ ] 3 Classic TA strategy files

---

## Step 1 — Wyckoff detection

### backend/engine/patterns/wyckoff.py
```python
"""
BLARE Wyckoff Pattern Detection
Implements Wyckoff accumulation and distribution phase detection.

Wyckoff Accumulation Phases:
  Phase A: Selling climax (SC), automatic rally (AR), secondary test (ST)
  Phase B: Building cause — range bound between SC and AR
  Phase C: Spring — false breakdown below support (the trap)
  Phase D: Signs of Strength (SOS), last point of support (LPS)
  Phase E: Markup — breakout and trend

Wyckoff Distribution is the mirror image.
"""
from typing import Optional, List
from engine.patterns.smc import find_swing_highs, find_swing_lows

def detect_range(candles: list, lookback: int = 60) -> Optional[dict]:
    """
    Detect if price is in a defined range (prerequisite for Wyckoff).
    Range = price oscillating between clear support and resistance.
    """
    if len(candles) < lookback:
        return None

    recent = candles[-lookback:]
    highs = [c["high"] for c in recent]
    lows = [c["low"] for c in recent]

    range_high = max(highs)
    range_low = min(lows)
    range_size_pct = (range_high - range_low) / range_low * 100

    # Need meaningful range — at least 2% for crypto, 0.5% for forex
    if range_size_pct < 0.5:
        return None

    # Check if price has touched both extremes multiple times (oscillation)
    touches_high = sum(1 for c in recent if c["high"] >= range_high * 0.998)
    touches_low = sum(1 for c in recent if c["low"] <= range_low * 1.002)

    if touches_high >= 2 and touches_low >= 2:
        return {
            "range_high": range_high,
            "range_low": range_low,
            "range_size_pct": round(range_size_pct, 2),
            "midpoint": (range_high + range_low) / 2,
            "touches_high": touches_high,
            "touches_low": touches_low,
        }
    return None

def detect_selling_climax(candles: list, lookback: int = 60) -> Optional[dict]:
    """
    Detect Selling Climax (SC) — Wyckoff Phase A.
    SC = wide-spread bearish candle on high volume after a downtrend.
    Followed quickly by an Automatic Rally (AR).
    """
    if len(candles) < lookback:
        return None

    recent = candles[-lookback:]
    avg_body = sum(abs(c["close"] - c["open"]) for c in recent) / len(recent)
    avg_vol = sum(c["volume"] for c in recent) / len(recent)

    # Look for climactic candle (large bearish + high volume)
    for i in range(5, len(recent) - 5):
        c = recent[i]
        body = abs(c["close"] - c["open"])
        is_bearish = c["close"] < c["open"]
        is_large = body >= avg_body * 2.5
        is_high_vol = c["volume"] >= avg_vol * 2.0

        if is_bearish and is_large and is_high_vol:
            # Check for subsequent rally (AR)
            post_candles = recent[i+1:i+6]
            if post_candles:
                post_high = max(c["high"] for c in post_candles)
                if post_high > c["close"] * 1.01:  # 1% rally after SC
                    return {
                        "type": "SC",
                        "candle": c,
                        "sc_low": c["low"],
                        "ar_high": post_high,
                        "index": i,
                        "description": f"Selling Climax at {c['low']:.5f}, AR at {post_high:.5f}"
                    }
    return None

def detect_spring(candles: list, range_data: dict, lookback: int = 10) -> Optional[dict]:
    """
    Detect Wyckoff Spring — Phase C.
    Spring = brief false breakdown below range support,
    quickly followed by recovery back inside range.
    This is the key entry signal in Wyckoff accumulation.
    """
    if not range_data or len(candles) < lookback:
        return None

    support = range_data["range_low"]
    current = candles[-1]
    recent = candles[-lookback:]

    # Find candle that pierced below support
    for i in range(len(recent) - 3):
        c = recent[i]
        if c["low"] < support * 0.999:  # pierced below support
            # Check recovery — next candles close back above support
            recovery = recent[i+1:i+4]
            if recovery and any(r["close"] > support for r in recovery):
                return {
                    "type": "SPRING",
                    "support_level": support,
                    "spring_low": c["low"],
                    "recovery_close": recovery[0]["close"],
                    "candle": c,
                    "description": f"Spring below {support:.5f}, recovered to {recovery[0]['close']:.5f}"
                }
    return None

def detect_utad(candles: list, range_data: dict) -> Optional[dict]:
    """
    Detect UTAD (Upthrust After Distribution) — mirror of Spring.
    False breakout above range resistance in distribution phase.
    """
    if not range_data or len(candles) < 10:
        return None

    resistance = range_data["range_high"]
    recent = candles[-10:]

    for i in range(len(recent) - 3):
        c = recent[i]
        if c["high"] > resistance * 1.001:  # pierced above resistance
            recovery = recent[i+1:i+4]
            if recovery and any(r["close"] < resistance for r in recovery):
                return {
                    "type": "UTAD",
                    "resistance_level": resistance,
                    "utad_high": c["high"],
                    "recovery_close": recovery[0]["close"],
                    "candle": c,
                    "description": f"UTAD above {resistance:.5f}, closed back at {recovery[0]['close']:.5f}"
                }
    return None

def detect_wyckoff(candles: list, strategy: dict) -> Optional[dict]:
    """
    Main Wyckoff detection entry point.
    Returns signal dict if Spring or UTAD detected in a valid range.
    """
    if len(candles) < 60:
        return None

    range_data = detect_range(candles, lookback=60)
    if not range_data:
        return None

    direction = strategy.get("direction", "both")

    # Bullish: look for Spring (accumulation)
    if direction in ("bullish", "long", "both"):
        spring = detect_spring(candles, range_data)
        if spring:
            entry = range_data["midpoint"]
            stop = spring["spring_low"] * 0.999
            target = range_data["range_high"] * 1.002
            return {
                "direction": "long",
                "entry": entry,
                "stop": stop,
                "target": target,
                "pattern_detail": spring["description"]
            }

    # Bearish: look for UTAD (distribution)
    if direction in ("bearish", "short", "both"):
        utad = detect_utad(candles, range_data)
        if utad:
            entry = range_data["midpoint"]
            stop = utad["utad_high"] * 1.001
            target = range_data["range_low"] * 0.998
            return {
                "direction": "short",
                "entry": entry,
                "stop": stop,
                "target": target,
                "pattern_detail": utad["description"]
            }

    return None
```

---

## Step 2 — Classic TA detection

### backend/engine/patterns/classic_ta.py
```python
"""
BLARE Classic Technical Analysis Pattern Detection
Detects traditional chart patterns using geometric price analysis.

Patterns:
  - Head and Shoulders (regular + inverse)
  - Double Top + Double Bottom
  - Triangles (ascending, descending, symmetrical)
  - Wedges (rising + falling)
  - Flags (bull + bear)
"""
from typing import Optional, List
from engine.patterns.smc import find_swing_highs, find_swing_lows

def detect_head_and_shoulders(candles: list, lookback: int = 60,
                               tolerance: float = 0.02) -> Optional[dict]:
    """
    Detect Head and Shoulders (H&S) — bearish reversal.
    Detect Inverse H&S — bullish reversal.

    H&S = 3 peaks where middle peak (head) is highest,
    left and right shoulders are roughly equal height.
    Neckline = line connecting the two troughs between peaks.
    """
    if len(candles) < lookback:
        return None

    recent = candles[-lookback:]
    highs = find_swing_highs(recent, lookback=5)
    lows = find_swing_lows(recent, lookback=5)

    # Need at least 3 swing highs for H&S
    if len(highs) >= 3:
        # Take last 3 swing highs
        sh = highs[-3:]
        left, head, right = sh[0]["price"], sh[1]["price"], sh[2]["price"]

        # Head must be highest
        if head > left and head > right:
            # Shoulders roughly equal (within tolerance)
            shoulder_diff = abs(left - right) / left
            if shoulder_diff <= tolerance:
                # Neckline approximate
                neckline = min(left, right) * 0.998
                return {
                    "type": "HS",
                    "direction": "bearish",
                    "left_shoulder": left,
                    "head": head,
                    "right_shoulder": right,
                    "neckline": neckline,
                    "target": neckline - (head - neckline),
                    "description": f"Head & Shoulders — head:{head:.5f} neckline:{neckline:.5f}"
                }

    # Inverse H&S — 3 swing lows
    if len(lows) >= 3:
        sl = lows[-3:]
        left, head, right = sl[0]["price"], sl[1]["price"], sl[2]["price"]

        if head < left and head < right:
            shoulder_diff = abs(left - right) / left
            if shoulder_diff <= tolerance:
                neckline = max(left, right) * 1.002
                return {
                    "type": "IHS",
                    "direction": "bullish",
                    "left_shoulder": left,
                    "head": head,
                    "right_shoulder": right,
                    "neckline": neckline,
                    "target": neckline + (neckline - head),
                    "description": f"Inverse H&S — head:{head:.5f} neckline:{neckline:.5f}"
                }
    return None

def detect_double_top_bottom(candles: list, lookback: int = 40,
                              tolerance: float = 0.015) -> Optional[dict]:
    """
    Detect Double Top (bearish) and Double Bottom (bullish).
    Two peaks/troughs at roughly the same price level.
    """
    if len(candles) < lookback:
        return None

    recent = candles[-lookback:]
    highs = find_swing_highs(recent, lookback=5)
    lows = find_swing_lows(recent, lookback=5)

    # Double Top
    if len(highs) >= 2:
        h1, h2 = highs[-2]["price"], highs[-1]["price"]
        if abs(h1 - h2) / h1 <= tolerance:
            neckline = min(c["low"] for c in recent[highs[-2]["index"]:highs[-1]["index"]+1])
            return {
                "type": "DT",
                "direction": "bearish",
                "top1": h1,
                "top2": h2,
                "neckline": neckline,
                "target": neckline - (h1 - neckline),
                "description": f"Double Top at {h1:.5f} / {h2:.5f}"
            }

    # Double Bottom
    if len(lows) >= 2:
        l1, l2 = lows[-2]["price"], lows[-1]["price"]
        if abs(l1 - l2) / l1 <= tolerance:
            neckline = max(c["high"] for c in recent[lows[-2]["index"]:lows[-1]["index"]+1])
            return {
                "type": "DB",
                "direction": "bullish",
                "bottom1": l1,
                "bottom2": l2,
                "neckline": neckline,
                "target": neckline + (neckline - l1),
                "description": f"Double Bottom at {l1:.5f} / {l2:.5f}"
            }
    return None

def detect_triangle(candles: list, lookback: int = 40) -> Optional[dict]:
    """
    Detect triangle patterns.
    Ascending: flat resistance + rising support → bullish bias.
    Descending: flat support + falling resistance → bearish bias.
    Symmetrical: converging highs + lows → breakout either direction.
    """
    if len(candles) < lookback:
        return None

    recent = candles[-lookback:]
    highs = find_swing_highs(recent, lookback=4)
    lows = find_swing_lows(recent, lookback=4)

    if len(highs) < 2 or len(lows) < 2:
        return None

    # Trend of highs and lows
    high_trend = highs[-1]["price"] - highs[-2]["price"]
    low_trend = lows[-1]["price"] - lows[-2]["price"]

    # Ascending triangle: flat highs + rising lows
    if abs(high_trend / highs[-1]["price"]) < 0.005 and low_trend > 0:
        return {
            "type": "TRIANGLE_ASC",
            "direction": "bullish",
            "resistance": highs[-1]["price"],
            "support": lows[-1]["price"],
            "target": highs[-1]["price"] + (highs[-1]["price"] - lows[-1]["price"]),
            "description": f"Ascending triangle — resistance:{highs[-1]['price']:.5f}"
        }

    # Descending triangle: flat lows + falling highs
    if abs(low_trend / lows[-1]["price"]) < 0.005 and high_trend < 0:
        return {
            "type": "TRIANGLE_DESC",
            "direction": "bearish",
            "resistance": highs[-1]["price"],
            "support": lows[-1]["price"],
            "target": lows[-1]["price"] - (highs[-1]["price"] - lows[-1]["price"]),
            "description": f"Descending triangle — support:{lows[-1]['price']:.5f}"
        }

    # Symmetrical: both converging
    if high_trend < 0 and low_trend > 0:
        apex = (highs[-1]["price"] + lows[-1]["price"]) / 2
        return {
            "type": "TRIANGLE_SYM",
            "direction": "neutral",
            "apex": apex,
            "description": f"Symmetrical triangle — apex:{apex:.5f}"
        }
    return None

def detect_wedge(candles: list, lookback: int = 40) -> Optional[dict]:
    """
    Detect wedge patterns.
    Rising wedge: both highs and lows rising but converging → bearish.
    Falling wedge: both falling but converging → bullish.
    """
    if len(candles) < lookback:
        return None

    recent = candles[-lookback:]
    highs = find_swing_highs(recent, lookback=4)
    lows = find_swing_lows(recent, lookback=4)

    if len(highs) < 2 or len(lows) < 2:
        return None

    high_trend = highs[-1]["price"] - highs[-2]["price"]
    low_trend = lows[-1]["price"] - lows[-2]["price"]

    # Rising wedge: both rising, lows rising faster (converging)
    if high_trend > 0 and low_trend > 0 and low_trend > high_trend:
        return {
            "type": "WEDGE_RISING",
            "direction": "bearish",
            "upper": highs[-1]["price"],
            "lower": lows[-1]["price"],
            "description": f"Rising wedge — bearish reversal expected"
        }

    # Falling wedge: both falling, highs falling faster (converging)
    if high_trend < 0 and low_trend < 0 and high_trend < low_trend:
        return {
            "type": "WEDGE_FALLING",
            "direction": "bullish",
            "upper": highs[-1]["price"],
            "lower": lows[-1]["price"],
            "description": f"Falling wedge — bullish reversal expected"
        }
    return None

def detect_flag(candles: list, lookback: int = 30) -> Optional[dict]:
    """
    Detect bull and bear flag patterns.
    Flag = strong impulse move followed by tight consolidation
    (slight retracement against the impulse).
    """
    if len(candles) < lookback:
        return None

    recent = candles[-lookback:]
    avg_body = sum(abs(c["close"] - c["open"]) for c in recent) / len(recent)

    # Find the impulse move (first ~40% of lookback)
    impulse_window = recent[:int(lookback * 0.4)]
    flag_window = recent[int(lookback * 0.4):]

    if not impulse_window or not flag_window:
        return None

    impulse_start = impulse_window[0]["close"]
    impulse_end = impulse_window[-1]["close"]
    impulse_move = impulse_end - impulse_start

    flag_high = max(c["high"] for c in flag_window)
    flag_low = min(c["low"] for c in flag_window)
    flag_range = flag_high - flag_low

    # Bull flag: impulse up + small bearish consolidation
    if impulse_move > avg_body * 3 and flag_range < abs(impulse_move) * 0.5:
        if flag_low > impulse_start:  # consolidation above impulse start
            return {
                "type": "FLAG_BULL",
                "direction": "bullish",
                "impulse_start": impulse_start,
                "impulse_end": impulse_end,
                "flag_high": flag_high,
                "flag_low": flag_low,
                "target": impulse_end + abs(impulse_move),
                "description": f"Bull flag — target:{impulse_end + abs(impulse_move):.5f}"
            }

    # Bear flag: impulse down + small bullish consolidation
    if impulse_move < -avg_body * 3 and flag_range < abs(impulse_move) * 0.5:
        if flag_high < impulse_start:
            return {
                "type": "FLAG_BEAR",
                "direction": "bearish",
                "impulse_start": impulse_start,
                "impulse_end": impulse_end,
                "flag_high": flag_high,
                "flag_low": flag_low,
                "target": impulse_end - abs(impulse_move),
                "description": f"Bear flag — target:{impulse_end - abs(impulse_move):.5f}"
            }
    return None

def detect_all(candles: list, strategy: dict) -> Optional[dict]:
    """Main classic TA detection entry point."""
    if len(candles) < 40:
        return None

    current = candles[-1]["close"]
    direction = strategy.get("direction", "both")

    hs = detect_head_and_shoulders(candles)
    dt = detect_double_top_bottom(candles)
    triangle = detect_triangle(candles)
    wedge = detect_wedge(candles)
    flag = detect_flag(candles)

    for pattern in [hs, dt, triangle, wedge, flag]:
        if not pattern:
            continue
        pat_dir = pattern.get("direction", "neutral")
        if pat_dir == "neutral":
            continue
        long_ok = pat_dir == "bullish" and direction in ("both", "long", "bullish")
        short_ok = pat_dir == "bearish" and direction in ("both", "short", "bearish")
        if not (long_ok or short_ok):
            continue

        target = pattern.get("target", 0)
        neckline = pattern.get("neckline", current)

        if long_ok and target > current:
            stop = pattern.get("support", pattern.get("lower", current * 0.98))
            return {"direction": "long", "entry": current,
                    "stop": stop, "target": target,
                    "pattern_detail": pattern["description"]}

        if short_ok and target < current:
            stop = pattern.get("resistance", pattern.get("upper", current * 1.02))
            return {"direction": "short", "entry": current,
                    "stop": stop, "target": target,
                    "pattern_detail": pattern["description"]}

    return None
```

---

## Step 3 — Update scanner to include all detectors

Add to `backend/engine/scanner.py` imports:
```python
from engine.patterns.wyckoff import detect_wyckoff
from engine.patterns.classic_ta import detect_all as detect_classic
```

Update `scan_instrument` to run all three:
```python
# Try each detector family in sequence
for detector, name in [
    (lambda c, s: detect_smc(c, s, timeframe), "smc"),
    (lambda c, s: detect_wyckoff(c, s), "wyckoff"),
    (lambda c, s: detect_classic(c, s), "classic_ta"),
]:
    result = detector(candles, strategy)
    if result:
        # build and save signal as before
        break
```

---

## Step 4 — Strategy files for Wyckoff + Classic TA

Create `strategies/wyckoff_spring.txt`,
`strategies/wyckoff_utad.txt`,
`strategies/classic_double_bottom.txt` following the same
`STRATEGY_TEMPLATE.md` format used in Session 03.

---

## Step 5 — Verify

```bash
curl http://localhost:8000/strategies/
# Should return 7+ strategies total

curl http://localhost:8000/signals/?limit=5
# Should start showing signals across all pattern families
```

Checklist:
- [ ] Wyckoff Spring + UTAD detecting correctly
- [ ] H&S + Double Top/Bottom working
- [ ] Triangles + Wedges + Flags detecting
- [ ] All 3 detector families integrated in scanner
- [ ] 7+ strategies loaded total

---

## Session 05 Complete

Commit message: `feat: session 05 — Wyckoff + Classic TA detection complete`

Next: **Session 06 — AI Validation Layer**
