"""
BLARE Classic Technical Analysis Pattern Detection
Head & Shoulders, Double Top/Bottom, Triangles, Wedges, Flags.
"""
from typing import Optional
from engine.patterns.smc import find_swing_highs, find_swing_lows


def detect_head_and_shoulders(candles: list, lookback: int = 60, tolerance: float = 0.02) -> Optional[dict]:
    if len(candles) < lookback:
        return None
    recent = candles[-lookback:]
    highs = find_swing_highs(recent, lookback=5)
    lows = find_swing_lows(recent, lookback=5)

    if len(highs) >= 3:
        left, head, right = highs[-3]["price"], highs[-2]["price"], highs[-1]["price"]
        if head > left and head > right and abs(left - right) / left <= tolerance:
            neckline = min(left, right) * 0.998
            return {"type": "HS", "direction": "bearish", "left_shoulder": left,
                    "head": head, "right_shoulder": right, "neckline": neckline,
                    "target": neckline - (head - neckline),
                    "description": f"Head & Shoulders head:{head:.5f} neckline:{neckline:.5f}"}

    if len(lows) >= 3:
        left, head, right = lows[-3]["price"], lows[-2]["price"], lows[-1]["price"]
        if head < left and head < right and abs(left - right) / left <= tolerance:
            neckline = max(left, right) * 1.002
            return {"type": "IHS", "direction": "bullish", "left_shoulder": left,
                    "head": head, "right_shoulder": right, "neckline": neckline,
                    "target": neckline + (neckline - head),
                    "description": f"Inverse H&S head:{head:.5f} neckline:{neckline:.5f}"}
    return None


def detect_double_top_bottom(candles: list, lookback: int = 40, tolerance: float = 0.015) -> Optional[dict]:
    if len(candles) < lookback:
        return None
    recent = candles[-lookback:]
    highs = find_swing_highs(recent, lookback=5)
    lows = find_swing_lows(recent, lookback=5)

    if len(highs) >= 2:
        h1, h2 = highs[-2]["price"], highs[-1]["price"]
        if abs(h1 - h2) / h1 <= tolerance:
            i1, i2 = highs[-2]["index"], highs[-1]["index"]
            neckline = min(c["low"] for c in recent[i1:i2+1])
            return {"type": "DT", "direction": "bearish", "top1": h1, "top2": h2,
                    "neckline": neckline, "target": neckline - (h1 - neckline),
                    "description": f"Double Top {h1:.5f}/{h2:.5f}"}

    if len(lows) >= 2:
        l1, l2 = lows[-2]["price"], lows[-1]["price"]
        if abs(l1 - l2) / l1 <= tolerance:
            i1, i2 = lows[-2]["index"], lows[-1]["index"]
            neckline = max(c["high"] for c in recent[i1:i2+1])
            return {"type": "DB", "direction": "bullish", "bottom1": l1, "bottom2": l2,
                    "neckline": neckline, "target": neckline + (neckline - l1),
                    "description": f"Double Bottom {l1:.5f}/{l2:.5f}"}
    return None


def detect_triangle(candles: list, lookback: int = 40) -> Optional[dict]:
    if len(candles) < lookback:
        return None
    recent = candles[-lookback:]
    highs = find_swing_highs(recent, lookback=4)
    lows = find_swing_lows(recent, lookback=4)
    if len(highs) < 2 or len(lows) < 2:
        return None
    high_trend = highs[-1]["price"] - highs[-2]["price"]
    low_trend = lows[-1]["price"] - lows[-2]["price"]

    if abs(high_trend / highs[-1]["price"]) < 0.005 and low_trend > 0:
        return {"type": "TRIANGLE_ASC", "direction": "bullish",
                "resistance": highs[-1]["price"], "support": lows[-1]["price"],
                "target": highs[-1]["price"] + (highs[-1]["price"] - lows[-1]["price"]),
                "description": f"Ascending triangle resistance:{highs[-1]['price']:.5f}"}

    if abs(low_trend / lows[-1]["price"]) < 0.005 and high_trend < 0:
        return {"type": "TRIANGLE_DESC", "direction": "bearish",
                "resistance": highs[-1]["price"], "support": lows[-1]["price"],
                "target": lows[-1]["price"] - (highs[-1]["price"] - lows[-1]["price"]),
                "description": f"Descending triangle support:{lows[-1]['price']:.5f}"}

    if high_trend < 0 and low_trend > 0:
        apex = (highs[-1]["price"] + lows[-1]["price"]) / 2
        return {"type": "TRIANGLE_SYM", "direction": "neutral", "apex": apex,
                "description": f"Symmetrical triangle apex:{apex:.5f}"}
    return None


def detect_wedge(candles: list, lookback: int = 40) -> Optional[dict]:
    if len(candles) < lookback:
        return None
    recent = candles[-lookback:]
    highs = find_swing_highs(recent, lookback=4)
    lows = find_swing_lows(recent, lookback=4)
    if len(highs) < 2 or len(lows) < 2:
        return None
    high_trend = highs[-1]["price"] - highs[-2]["price"]
    low_trend = lows[-1]["price"] - lows[-2]["price"]

    if high_trend > 0 and low_trend > 0 and low_trend > high_trend:
        return {"type": "WEDGE_RISING", "direction": "bearish",
                "upper": highs[-1]["price"], "lower": lows[-1]["price"],
                "description": "Rising wedge — bearish reversal expected"}

    if high_trend < 0 and low_trend < 0 and high_trend < low_trend:
        return {"type": "WEDGE_FALLING", "direction": "bullish",
                "upper": highs[-1]["price"], "lower": lows[-1]["price"],
                "description": "Falling wedge — bullish reversal expected"}
    return None


def detect_flag(candles: list, lookback: int = 30) -> Optional[dict]:
    if len(candles) < lookback:
        return None
    recent = candles[-lookback:]
    avg_body = sum(abs(c["close"] - c["open"]) for c in recent) / len(recent)
    split = int(lookback * 0.4)
    impulse_w, flag_w = recent[:split], recent[split:]
    if not impulse_w or not flag_w:
        return None

    impulse_start = impulse_w[0]["close"]
    impulse_end = impulse_w[-1]["close"]
    impulse_move = impulse_end - impulse_start
    flag_high = max(c["high"] for c in flag_w)
    flag_low = min(c["low"] for c in flag_w)
    flag_range = flag_high - flag_low

    if impulse_move > avg_body * 3 and flag_range < abs(impulse_move) * 0.5 and flag_low > impulse_start:
        return {"type": "FLAG_BULL", "direction": "bullish",
                "impulse_end": impulse_end, "flag_high": flag_high, "flag_low": flag_low,
                "target": impulse_end + abs(impulse_move),
                "description": f"Bull flag target:{impulse_end + abs(impulse_move):.5f}"}

    if impulse_move < -avg_body * 3 and flag_range < abs(impulse_move) * 0.5 and flag_high < impulse_start:
        return {"type": "FLAG_BEAR", "direction": "bearish",
                "impulse_end": impulse_end, "flag_high": flag_high, "flag_low": flag_low,
                "target": impulse_end - abs(impulse_move),
                "description": f"Bear flag target:{impulse_end - abs(impulse_move):.5f}"}
    return None


def detect_all(candles: list, strategy: dict) -> Optional[dict]:
    if len(candles) < 40:
        return None
    current = candles[-1]["close"]
    direction = strategy.get("direction", "both")

    for pattern in [detect_head_and_shoulders(candles), detect_double_top_bottom(candles),
                    detect_triangle(candles), detect_wedge(candles), detect_flag(candles)]:
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
        if long_ok and target > current:
            stop = pattern.get("support", pattern.get("lower", current * 0.98))
            return {"direction": "long", "entry": current, "stop": stop, "target": target,
                    "pattern_detail": pattern["description"]}
        if short_ok and target < current:
            stop = pattern.get("resistance", pattern.get("upper", current * 1.02))
            return {"direction": "short", "entry": current, "stop": stop, "target": target,
                    "pattern_detail": pattern["description"]}
    return None
