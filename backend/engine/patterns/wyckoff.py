"""
BLARE Wyckoff Pattern Detection
Implements Wyckoff accumulation and distribution phase detection.
"""
from typing import Optional
from engine.patterns.smc import find_swing_highs, find_swing_lows


def detect_range(candles: list, lookback: int = 60) -> Optional[dict]:
    if len(candles) < lookback:
        return None
    recent = candles[-lookback:]
    range_high = max(c["high"] for c in recent)
    range_low = min(c["low"] for c in recent)
    range_size_pct = (range_high - range_low) / range_low * 100
    if range_size_pct < 0.5:
        return None
    touches_high = sum(1 for c in recent if c["high"] >= range_high * 0.998)
    touches_low = sum(1 for c in recent if c["low"] <= range_low * 1.002)
    if touches_high >= 2 and touches_low >= 2:
        return {"range_high": range_high, "range_low": range_low,
                "range_size_pct": round(range_size_pct, 2),
                "midpoint": (range_high + range_low) / 2,
                "touches_high": touches_high, "touches_low": touches_low}
    return None


def detect_selling_climax(candles: list, lookback: int = 60) -> Optional[dict]:
    if len(candles) < lookback:
        return None
    recent = candles[-lookback:]
    avg_body = sum(abs(c["close"] - c["open"]) for c in recent) / len(recent)
    avg_vol = sum(c["volume"] for c in recent) / len(recent)
    for i in range(5, len(recent) - 5):
        c = recent[i]
        body = abs(c["close"] - c["open"])
        if (c["close"] < c["open"] and body >= avg_body * 2.5 and
                c["volume"] >= avg_vol * 2.0):
            post = recent[i+1:i+6]
            if post and max(p["high"] for p in post) > c["close"] * 1.01:
                ar_high = max(p["high"] for p in post)
                return {"type": "SC", "candle": c, "sc_low": c["low"],
                        "ar_high": ar_high, "index": i,
                        "description": f"Selling Climax at {c['low']:.5f}, AR at {ar_high:.5f}"}
    return None


def detect_spring(candles: list, range_data: dict, lookback: int = 10) -> Optional[dict]:
    if not range_data or len(candles) < lookback:
        return None
    support = range_data["range_low"]
    recent = candles[-lookback:]
    for i in range(len(recent) - 3):
        c = recent[i]
        if c["low"] < support * 0.999:
            recovery = recent[i+1:i+4]
            if recovery and any(r["close"] > support for r in recovery):
                return {"type": "SPRING", "support_level": support,
                        "spring_low": c["low"], "recovery_close": recovery[0]["close"],
                        "candle": c,
                        "description": f"Spring below {support:.5f}, recovered to {recovery[0]['close']:.5f}"}
    return None


def detect_utad(candles: list, range_data: dict) -> Optional[dict]:
    if not range_data or len(candles) < 10:
        return None
    resistance = range_data["range_high"]
    recent = candles[-10:]
    for i in range(len(recent) - 3):
        c = recent[i]
        if c["high"] > resistance * 1.001:
            recovery = recent[i+1:i+4]
            if recovery and any(r["close"] < resistance for r in recovery):
                return {"type": "UTAD", "resistance_level": resistance,
                        "utad_high": c["high"], "recovery_close": recovery[0]["close"],
                        "candle": c,
                        "description": f"UTAD above {resistance:.5f}, closed back at {recovery[0]['close']:.5f}"}
    return None


def detect_wyckoff(candles: list, strategy: dict) -> Optional[dict]:
    if len(candles) < 60:
        return None
    range_data = detect_range(candles, lookback=60)
    if not range_data:
        return None
    direction = strategy.get("direction", "both")

    if direction in ("bullish", "long", "both"):
        spring = detect_spring(candles, range_data)
        if spring:
            entry = range_data["midpoint"]
            stop = spring["spring_low"] * 0.999
            target = range_data["range_high"] * 1.002
            return {"direction": "long", "entry": entry, "stop": stop,
                    "target": target, "pattern_detail": spring["description"]}

    if direction in ("bearish", "short", "both"):
        utad = detect_utad(candles, range_data)
        if utad:
            entry = range_data["midpoint"]
            stop = utad["utad_high"] * 1.001
            target = range_data["range_low"] * 0.998
            return {"direction": "short", "entry": entry, "stop": stop,
                    "target": target, "pattern_detail": utad["description"]}

    return None
