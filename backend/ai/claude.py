"""
BLARE Claude AI Integration
Sends signal context to Claude for pattern validation and trade narrative.
Caches results per symbol+timeframe+direction for 1 hour to reduce API calls.
"""
import json
import time
import asyncio
import anthropic
from config.settings import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Cache: key -> (result, timestamp)
_cache: dict = {}
_CACHE_TTL = 3600  # 1 hour

SYSTEM_PROMPT = """You are a senior institutional trader and technical analyst
with 15 years of experience in crypto and forex markets.

You specialize in Smart Money Concepts (SMC), ICT methodology,
Wyckoff analysis, and classic technical analysis.

Your job is to review trading setups detected by an automated system
and provide honest, concise analysis. You are critical and skeptical —
you only validate setups that are genuinely high quality.

Always respond in valid JSON only. No markdown, no extra text."""


def build_context(signal_data: dict, candles: list, strategy: dict) -> str:
    recent_candles = candles[-10:]
    candle_summary = "\n".join([
        f"  {i+1}. O:{c['open']:.5f} H:{c['high']:.5f} L:{c['low']:.5f} C:{c['close']:.5f} V:{c['volume']:.0f}"
        for i, c in enumerate(recent_candles)
    ])
    htf_closes = [c["close"] for c in candles[-20:]]
    htf_trend = "bullish" if htf_closes[-1] > htf_closes[0] else "bearish"
    htf_change_pct = ((htf_closes[-1] - htf_closes[0]) / htf_closes[0]) * 100

    return f"""SETUP TO REVIEW:
Symbol: {signal_data['symbol']} | Market: {signal_data['market']}
Timeframe: {signal_data['timeframe']} | Direction: {signal_data['direction'].upper()}
Pattern: {signal_data['pattern']}
Pattern detail: {signal_data.get('pattern_detail', 'N/A')}

TRADE LEVELS:
Entry: {signal_data['entry']:.5f} | Stop: {signal_data['stop']:.5f} | Target: {signal_data['target']:.5f}
R:R: {signal_data.get('rr', 0):.1f}:1

STRATEGY: {strategy.get('concept', 'N/A')}
HTF trend: {htf_trend} ({htf_change_pct:+.2f}% over 20 candles)

LAST 10 CANDLES (oldest to newest):
{candle_summary}

Respond with JSON only:
{{"valid": true/false, "narrative": "2-3 sentence trade rationale", "strengths": ["str1"], "weaknesses": ["wk1"], "htf_aligned": true/false, "recommendation": "take"/"skip"/"wait"}}"""


async def validate_signal(signal_data: dict, candles: list, strategy: dict) -> dict:
    cache_key = f"{signal_data['symbol']}_{signal_data['timeframe']}_{signal_data['direction']}_{signal_data['pattern']}"
    now = time.time()

    cached = _cache.get(cache_key)
    if cached and now - cached[1] < _CACHE_TTL:
        print(f"[Claude] Cache hit: {cache_key}")
        return cached[0]

    try:
        context = build_context(signal_data, candles, strategy)
        response = await asyncio.to_thread(
            client.messages.create,
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": context}]
        )
        text = response.content[0].text.strip()
        result = json.loads(text)
        _cache[cache_key] = (result, now)
        print(f"[Claude] {signal_data['symbol']} {signal_data['direction']}: "
              f"valid={result.get('valid')} rec={result.get('recommendation')}")
        return result
    except Exception as e:
        print(f"[Claude] Error validating signal: {e!r}")
        return {"valid": True, "narrative": "",
                "strengths": [], "weaknesses": [],
                "htf_aligned": True, "recommendation": "proceed"}
