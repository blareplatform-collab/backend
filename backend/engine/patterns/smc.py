"""
BLARE SMC / ICT Pattern Detection Library
Implements the core Smart Money Concepts used in ICT methodology.
"""
from typing import Optional, List


def find_swing_highs(candles: list, lookback: int = 5) -> list:
    highs = []
    for i in range(lookback, len(candles) - lookback):
        window_highs = [c["high"] for c in candles[i-lookback:i+lookback+1]]
        if candles[i]["high"] == max(window_highs):
            highs.append({"index": i, "price": candles[i]["high"], "candle": candles[i]})
    return highs


def find_swing_lows(candles: list, lookback: int = 5) -> list:
    lows = []
    for i in range(lookback, len(candles) - lookback):
        window_lows = [c["low"] for c in candles[i-lookback:i+lookback+1]]
        if candles[i]["low"] == min(window_lows):
            lows.append({"index": i, "price": candles[i]["low"], "candle": candles[i]})
    return lows


# Keep single-result aliases for backward compat
def find_swing_high(candles: list, lookback: int = 20) -> Optional[dict]:
    results = find_swing_highs(candles[-lookback:] if len(candles) >= lookback else candles, lookback=3)
    return results[-1] if results else None


def find_swing_low(candles: list, lookback: int = 20) -> Optional[dict]:
    results = find_swing_lows(candles[-lookback:] if len(candles) >= lookback else candles, lookback=3)
    return results[-1] if results else None


def detect_bos(candles: list, lookback: int = 20) -> Optional[dict]:
    """Break of Structure — continuation signal."""
    if len(candles) < lookback + 5:
        return None
    recent = candles[-lookback:]
    current = candles[-1]
    swing_highs = find_swing_highs(recent[:-3], lookback=3)
    swing_lows = find_swing_lows(recent[:-3], lookback=3)
    if swing_highs:
        last_high = swing_highs[-1]["price"]
        if current["close"] > last_high:
            return {"type": "BOS", "direction": "bullish", "level": last_high,
                    "candle": current, "description": f"BOS above {last_high:.5f}"}
    if swing_lows:
        last_low = swing_lows[-1]["price"]
        if current["close"] < last_low:
            return {"type": "BOS", "direction": "bearish", "level": last_low,
                    "candle": current, "description": f"BOS below {last_low:.5f}"}
    return None


def detect_choch(candles: list, lookback: int = 30) -> Optional[dict]:
    """Change of Character — first break against prevailing trend."""
    if len(candles) < lookback + 5:
        return None
    recent = candles[-lookback:]
    midpoint = len(recent) // 2
    first_avg = sum(c["close"] for c in recent[:midpoint]) / midpoint
    second_avg = sum(c["close"] for c in recent[midpoint:]) / (len(recent) - midpoint)
    current = candles[-1]
    swing_highs = find_swing_highs(recent[:-3], lookback=3)
    swing_lows = find_swing_lows(recent[:-3], lookback=3)
    if second_avg < first_avg and swing_highs:
        last_high = swing_highs[-1]["price"]
        if current["close"] > last_high:
            return {"type": "CHoCH", "direction": "bullish", "level": last_high,
                    "candle": current, "description": f"CHoCH bullish above {last_high:.5f}"}
    if second_avg > first_avg and swing_lows:
        last_low = swing_lows[-1]["price"]
        if current["close"] < last_low:
            return {"type": "CHoCH", "direction": "bearish", "level": last_low,
                    "candle": current, "description": f"CHoCH bearish below {last_low:.5f}"}
    return None


def detect_fvg(candles: list, min_gap_pct: float = 0.05) -> List[dict]:
    """Detect unfilled Fair Value Gaps."""
    fvgs = []
    if len(candles) < 3:
        return fvgs
    for i in range(2, len(candles)):
        c1, c3 = candles[i - 2], candles[i]
        # Bullish FVG
        if c3["low"] > c1["high"]:
            gap_size = (c3["low"] - c1["high"]) / c1["high"] * 100
            if gap_size >= min_gap_pct:
                filled = any(c["low"] <= c3["low"] and c["high"] >= c1["high"] for c in candles[i+1:])
                if not filled:
                    fvgs.append({"type": "FVG", "direction": "bullish",
                                 "upper": c3["low"], "lower": c1["high"],
                                 "midpoint": (c3["low"] + c1["high"]) / 2,
                                 "gap_pct": round(gap_size, 3), "index": i,
                                 "candle": c3, "filled": False,
                                 "description": f"Bullish FVG {c1['high']:.5f}-{c3['low']:.5f}"})
        # Bearish FVG
        if c3["high"] < c1["low"]:
            gap_size = (c1["low"] - c3["high"]) / c1["low"] * 100
            if gap_size >= min_gap_pct:
                filled = any(c["high"] >= c3["high"] and c["low"] <= c1["low"] for c in candles[i+1:])
                if not filled:
                    fvgs.append({"type": "FVG", "direction": "bearish",
                                 "upper": c1["low"], "lower": c3["high"],
                                 "midpoint": (c1["low"] + c3["high"]) / 2,
                                 "gap_pct": round(gap_size, 3), "index": i,
                                 "candle": c3, "filled": False,
                                 "description": f"Bearish FVG {c3['high']:.5f}-{c1['low']:.5f}"})
    return sorted(fvgs, key=lambda x: x["index"], reverse=True)


def detect_order_block(candles: list, lookback: int = 50) -> List[dict]:
    """Detect Order Blocks — last opposing candle before impulsive move."""
    obs = []
    if len(candles) < lookback:
        return obs
    recent = candles[-lookback:]
    avg_body = sum(abs(c["close"] - c["open"]) for c in recent) / len(recent)
    for i in range(1, len(recent) - 1):
        cur, nxt = recent[i], recent[i + 1]
        nxt_body = abs(nxt["close"] - nxt["open"])
        if cur["close"] < cur["open"] and nxt["close"] > nxt["open"] and nxt_body >= avg_body * 2:
            obs.append({"type": "OB", "direction": "bullish",
                        "upper": cur["open"], "lower": cur["close"],
                        "index": i, "candle": cur,
                        "description": f"Bullish OB {cur['close']:.5f}-{cur['open']:.5f}"})
        if cur["close"] > cur["open"] and nxt["close"] < nxt["open"] and nxt_body >= avg_body * 2:
            obs.append({"type": "OB", "direction": "bearish",
                        "upper": cur["close"], "lower": cur["open"],
                        "index": i, "candle": cur,
                        "description": f"Bearish OB {cur['open']:.5f}-{cur['close']:.5f}"})
    return sorted(obs, key=lambda x: x["index"], reverse=True)


def detect_liquidity_sweep(candles: list, lookback: int = 20, buffer_pct: float = 0.1) -> Optional[dict]:
    """Detect liquidity sweep — wick beyond level then close back inside."""
    if len(candles) < lookback + 3:
        return None
    recent = candles[-lookback - 3:-3]
    current = candles[-1]
    swing_highs = find_swing_highs(recent, lookback=3)
    swing_lows = find_swing_lows(recent, lookback=3)
    if swing_highs:
        last_high = swing_highs[-1]["price"]
        buffer = last_high * (buffer_pct / 100)
        if current["high"] > last_high + buffer and current["close"] < last_high:
            return {"type": "SWEEP", "direction": "bearish", "swept_level": last_high,
                    "sweep_high": current["high"], "candle": current,
                    "description": f"Sweep above {last_high:.5f}, closed {current['close']:.5f}"}
    if swing_lows:
        last_low = swing_lows[-1]["price"]
        buffer = last_low * (buffer_pct / 100)
        if current["low"] < last_low - buffer and current["close"] > last_low:
            return {"type": "SWEEP", "direction": "bullish", "swept_level": last_low,
                    "sweep_low": current["low"], "candle": current,
                    "description": f"Sweep below {last_low:.5f}, closed {current['close']:.5f}"}
    return None


def get_premium_discount_zone(candles: list, lookback: int = 50) -> dict:
    """Calculate premium/discount zones relative to range equilibrium."""
    if len(candles) < lookback:
        return {}
    recent = candles[-lookback:]
    high = max(c["high"] for c in recent)
    low = min(c["low"] for c in recent)
    eq = (high + low) / 2
    current_close = candles[-1]["close"]
    zone = "premium" if current_close > eq else "discount"
    pct_from_eq = ((current_close - eq) / eq) * 100
    return {"high": high, "low": low, "equilibrium": eq,
            "current_zone": zone, "pct_from_equilibrium": round(pct_from_eq, 2),
            "description": f"Price in {zone} zone, {abs(pct_from_eq):.1f}% from EQ"}


def detect_all(candles: list, strategy: dict, timeframe: str) -> Optional[dict]:
    """Main entry point called by scanner for every instrument + strategy."""
    if len(candles) < 50:
        return None

    direction = strategy.get("direction", "both")
    sweep = detect_liquidity_sweep(candles)
    fvgs = detect_fvg(candles)
    choch = detect_choch(candles)
    obs = detect_order_block(candles)
    current_price = candles[-1]["close"]

    # Liquidity Sweep + FVG
    if sweep and fvgs:
        sweep_dir = sweep["direction"]
        if direction in ("both", sweep_dir):
            matching = [f for f in fvgs if f["direction"] == sweep_dir]
            if matching:
                fvg = matching[0]
                if sweep_dir == "bullish":
                    entry = fvg["upper"]
                    stop = sweep["sweep_low"] * 0.999
                    return {"direction": "long", "entry": entry, "stop": stop,
                            "target": current_price + (entry - stop) * 2.5,
                            "pattern_detail": f"{sweep['description']} + {fvg['description']}"}
                else:
                    entry = fvg["lower"]
                    stop = sweep["sweep_high"] * 1.001
                    return {"direction": "short", "entry": entry, "stop": stop,
                            "target": current_price - (stop - entry) * 2.5,
                            "pattern_detail": f"{sweep['description']} + {fvg['description']}"}

    # CHoCH + Order Block
    if choch and obs:
        choch_dir = choch["direction"]
        if direction in ("both", choch_dir):
            matching = [o for o in obs if o["direction"] == choch_dir]
            if matching:
                ob = matching[0]
                if choch_dir == "bullish":
                    entry = ob["upper"]
                    stop = ob["lower"] * 0.999
                    return {"direction": "long", "entry": entry, "stop": stop,
                            "target": entry + (entry - stop) * 2.5,
                            "pattern_detail": f"{choch['description']} + {ob['description']}"}
                else:
                    entry = ob["lower"]
                    stop = ob["upper"] * 1.001
                    return {"direction": "short", "entry": entry, "stop": stop,
                            "target": entry - (stop - entry) * 2.5,
                            "pattern_detail": f"{choch['description']} + {ob['description']}"}

    return None
