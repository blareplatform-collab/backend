# BLARE — Session 06: AI Validation Layer

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to build
Prerequisite: Session 05 complete

---

## Context

This session wires Claude and DeepSeek into every signal.
Every pattern match now gets validated by AI before firing.
Claude writes the trade narrative. DeepSeek scores confidence 0-100.
The confidence score drives position sizing automatically.

---

## Goals

- [ ] Claude validates every signal + writes trade narrative
- [ ] DeepSeek scores confidence 0-100
- [ ] Position sizing based on confidence score
- [ ] Signals below 50 confidence are dropped
- [ ] Full signal card data complete (all fields populated)
- [ ] AI prompts engineered specifically for trading context

---

## Step 1 — Claude integration

### backend/ai/claude.py
```python
"""
BLARE Claude AI Integration
Sends signal context to Claude for pattern validation and trade narrative.
Claude acts as a senior trader reviewing the setup.
"""
import anthropic
from config.settings import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a senior institutional trader and technical analyst
with 15 years of experience in crypto and forex markets.

You specialize in Smart Money Concepts (SMC), ICT methodology, 
Wyckoff analysis, and classic technical analysis.

Your job is to review trading setups detected by an automated system
and provide honest, concise analysis. You are critical and skeptical —
you only validate setups that are genuinely high quality.

Always respond in valid JSON only. No markdown, no extra text.
"""

def build_context(signal_data: dict, candles: list, strategy: dict) -> str:
    """Build the context string sent to Claude for analysis."""
    recent_candles = candles[-10:]
    candle_summary = "\n".join([
        f"  {i+1}. O:{c['open']:.5f} H:{c['high']:.5f} "
        f"L:{c['low']:.5f} C:{c['close']:.5f} V:{c['volume']:.0f}"
        for i, c in enumerate(recent_candles)
    ])

    # HTF trend (daily closes)
    htf_closes = [c["close"] for c in candles[-20:]]
    htf_trend = "bullish" if htf_closes[-1] > htf_closes[0] else "bearish"
    htf_change_pct = ((htf_closes[-1] - htf_closes[0]) / htf_closes[0]) * 100

    return f"""
SETUP TO REVIEW:

Symbol: {signal_data['symbol']}
Market: {signal_data['market']}
Timeframe: {signal_data['timeframe']}
Direction: {signal_data['direction'].upper()}
Pattern detected: {signal_data['pattern']}
Pattern detail: {signal_data.get('pattern_detail', 'N/A')}

TRADE LEVELS:
Entry: {signal_data['entry']:.5f}
Stop Loss: {signal_data['stop']:.5f}
Target: {signal_data['target']:.5f}
Risk/Reward: {signal_data.get('rr', 0):.1f}:1

STRATEGY CONCEPT:
{strategy.get('concept', 'N/A')}

MARKET CONTEXT:
HTF trend ({signal_data['timeframe']}): {htf_trend} ({htf_change_pct:+.2f}% over 20 candles)

LAST 10 CANDLES (oldest to newest):
{candle_summary}

Respond with JSON only in this exact format:
{{
  "valid": true/false,
  "narrative": "2-3 sentence trade rationale as a senior trader would write it",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1"],
  "htf_aligned": true/false,
  "recommendation": "take" / "skip" / "wait"
}}
"""

async def validate_signal(signal_data: dict, candles: list,
                           strategy: dict) -> dict:
    """
    Send signal to Claude for validation.
    Returns analysis dict with narrative and recommendation.
    """
    try:
        context = build_context(signal_data, candles, strategy)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": context}]
        )
        import json
        text = response.content[0].text.strip()
        result = json.loads(text)
        print(f"[Claude] {signal_data['symbol']} {signal_data['direction']}: "
              f"valid={result.get('valid')} rec={result.get('recommendation')}")
        return result
    except Exception as e:
        print(f"[Claude] Error validating signal: {e}")
        return {
            "valid": False,
            "narrative": "AI validation unavailable",
            "strengths": [],
            "weaknesses": ["Validation error"],
            "htf_aligned": False,
            "recommendation": "skip"
        }
```

---

## Step 2 — DeepSeek confidence scoring

### backend/ai/deepseek.py
```python
"""
BLARE DeepSeek Integration
Fast confidence scoring for trading signals (0-100).
Complements Claude's qualitative analysis with a numeric score.
"""
import httpx
import json
from config.settings import DEEPSEEK_API_KEY

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

SYSTEM_PROMPT = """You are a quantitative trading model that scores 
trading setups on a scale of 0-100 based on setup quality.

Scoring criteria:
- Pattern clarity (0-25): How clear and textbook is the pattern?
- Structure alignment (0-25): Does higher timeframe agree?
- Risk/reward (0-25): Is the R:R favorable (2:1 minimum)?
- Entry precision (0-25): Is the entry at a logical level?

Be strict. Most setups score between 40-75. 
Only exceptional setups score above 85.
Setups with R:R below 2:1 cannot score above 50.

Respond with JSON only:
{"score": 0-100, "breakdown": {"pattern": 0-25, "structure": 0-25, "rr": 0-25, "entry": 0-25}}
"""

async def score_signal(signal_data: dict, claude_result: dict) -> dict:
    """
    Score a signal 0-100 using DeepSeek.
    Takes Claude's analysis as additional context.
    """
    try:
        prompt = f"""
Rate this trading setup:

Symbol: {signal_data['symbol']} | Direction: {signal_data['direction'].upper()}
Pattern: {signal_data['pattern']} | Timeframe: {signal_data['timeframe']}
Entry: {signal_data['entry']:.5f}
Stop: {signal_data['stop']:.5f}  
Target: {signal_data['target']:.5f}
R:R: {signal_data.get('rr', 0):.1f}:1

Senior trader assessment: {claude_result.get('narrative', 'N/A')}
HTF aligned: {claude_result.get('htf_aligned', False)}
Strengths: {', '.join(claude_result.get('strengths', []))}
Weaknesses: {', '.join(claude_result.get('weaknesses', []))}
"""
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.1  # low temperature for consistent scoring
        }
        async with httpx.AsyncClient() as client:
            res = await client.post(
                DEEPSEEK_URL, headers=headers,
                json=payload, timeout=15
            )
            res.raise_for_status()
            data = res.json()
            text = data["choices"][0]["message"]["content"].strip()
            result = json.loads(text)
            score = result.get("score", 0)
            print(f"[DeepSeek] {signal_data['symbol']}: score={score}")
            return result
    except Exception as e:
        print(f"[DeepSeek] Error scoring signal: {e}")
        return {"score": 0, "breakdown": {}}
```

---

## Step 3 — Validator orchestrator

### backend/ai/validator.py
```python
"""
BLARE AI Validator
Orchestrates Claude + DeepSeek validation for every signal.
Applies confidence-based position sizing.
Drops signals below minimum confidence threshold.
"""
from ai.claude import validate_signal
from ai.deepseek import score_signal
from models.signal import Signal

MIN_CONFIDENCE = 50  # signals below this are dropped

# Position sizing by confidence band
CONFIDENCE_RISK = {
    (86, 100): 1.5,  # high confidence → 1.5% risk
    (71, 85):  1.0,  # medium confidence → 1.0% risk
    (51, 70):  0.5,  # low-medium → 0.5% risk
    (0,  50):  0.0,  # below threshold → skip
}

def get_position_size(confidence: int) -> float:
    """Map confidence score to position size percentage."""
    for (low, high), size in CONFIDENCE_RISK.items():
        if low <= confidence <= high:
            return size
    return 0.0

async def validate_and_enrich(signal: Signal, candles: list,
                               strategy: dict) -> Signal | None:
    """
    Run full AI validation on a signal.
    Returns enriched Signal if it passes, None if dropped.
    """
    signal_data = signal.to_dict()

    # Claude validation
    claude_result = await validate_signal(signal_data, candles, strategy)

    # Drop immediately if Claude says skip
    if claude_result.get("recommendation") == "skip":
        print(f"[Validator] Signal dropped by Claude: {signal.symbol}")
        return None

    # DeepSeek confidence score
    score_result = await score_signal(signal_data, claude_result)
    confidence = score_result.get("score", 0)

    # Drop if below minimum confidence
    if confidence < MIN_CONFIDENCE:
        print(f"[Validator] Signal dropped — confidence {confidence} < {MIN_CONFIDENCE}")
        return None

    # Enrich signal with AI data
    signal.confidence = confidence
    signal.ai_note = claude_result.get("narrative", "")
    signal.position_size_pct = get_position_size(confidence)

    print(f"[Validator] Signal APPROVED: {signal.symbol} "
          f"{signal.direction.upper()} confidence:{confidence} "
          f"size:{signal.position_size_pct}%")

    return signal
```

---

## Step 4 — Wire validator into scanner

Update `backend/engine/scanner.py` to use validator:

```python
from ai.validator import validate_and_enrich

# Inside scan_instrument, replace the direct save with:
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

    # AI validation (async)
    enriched = await validate_and_enrich(signal, candles, strategy)
    if enriched:
        _recent_signals[dedup_key] = now
        await save_signal(enriched)
```

---

## Step 5 — Verify

```bash
# Watch logs when scanner runs — you should see:
# [Claude] BTC/USDT long: valid=True rec=take
# [DeepSeek] BTC/USDT: score=78
# [Validator] Signal APPROVED: BTC/USDT LONG confidence:78 size:1.0%

# Check a signal in Firestore — should have ai_note and confidence populated
curl http://localhost:8000/signals/?limit=3
```

Checklist:
- [ ] Every signal runs through Claude before saving
- [ ] Every signal gets DeepSeek confidence score
- [ ] Signals below 50 are dropped silently
- [ ] Signal cards have ai_note + confidence + position_size_pct filled
- [ ] Logs showing AI validation flow clearly

---

## Session 06 Complete

Commit message: `feat: session 06 — AI validation layer complete`

Next: **Session 07 — Execution Engine**
