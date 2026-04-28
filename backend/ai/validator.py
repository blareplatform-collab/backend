"""
BLARE AI Validator
Orchestrates Claude + DeepSeek validation for every signal.
Applies confidence-based position sizing.
Drops signals below minimum confidence threshold.
"""
from ai.claude import validate_signal
from ai.deepseek import score_signal
from models.signal import Signal

MIN_CONFIDENCE = 50

CONFIDENCE_RISK = {
    (86, 100): 1.5,
    (71, 85):  1.0,
    (51, 70):  0.5,
    (0,  50):  0.0,
}


def get_position_size(confidence: int) -> float:
    for (low, high), size in CONFIDENCE_RISK.items():
        if low <= confidence <= high:
            return size
    return 0.0


async def validate_and_enrich(signal: Signal, candles: list, strategy: dict):
    signal_data = signal.to_dict()

    try:
        claude_result = await validate_signal(signal_data, candles, strategy)
        if claude_result.get("recommendation") == "skip":
            print(f"[Validator] Signal dropped by Claude: {signal.symbol}")
            return None
    except Exception as e:
        print(f"[Validator] Claude unavailable ({e}) — passing signal through")
        claude_result = {"recommendation": "proceed", "narrative": ""}

    try:
        score_result = await score_signal(signal_data, claude_result)
        confidence = score_result.get("score", 0)
    except Exception as e:
        print(f"[Validator] DeepSeek unavailable ({e}) — using default confidence 65")
        confidence = 65

    if confidence < MIN_CONFIDENCE:
        print(f"[Validator] Signal dropped — confidence {confidence} < {MIN_CONFIDENCE}")
        return None

    signal.confidence = confidence
    signal.ai_note = claude_result.get("narrative", "")
    signal.position_size_pct = get_position_size(confidence)

    print(f"[Validator] Signal APPROVED: {signal.symbol} {signal.direction.upper()} "
          f"confidence:{confidence} size:{signal.position_size_pct}%")
    return signal
