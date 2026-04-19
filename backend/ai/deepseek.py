"""
BLARE DeepSeek Integration
Fast confidence scoring for trading signals (0-100).
"""
import json
import httpx
from config.settings import DEEPSEEK_API_KEY

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

SYSTEM_PROMPT = """You are a quantitative trading model that scores trading setups 0-100.

Scoring criteria:
- Pattern clarity (0-25): How clear and textbook is the pattern?
- Structure alignment (0-25): Does higher timeframe agree?
- Risk/reward (0-25): Is R:R favorable (2:1 minimum)?
- Entry precision (0-25): Is the entry at a logical level?

Be strict. Most setups score 40-75. Only exceptional setups score above 85.
Setups with R:R below 2:1 cannot score above 50.

Respond with JSON only: {"score": 0-100, "breakdown": {"pattern": 0-25, "structure": 0-25, "rr": 0-25, "entry": 0-25}}"""


async def score_signal(signal_data: dict, claude_result: dict) -> dict:
    try:
        prompt = f"""Rate this trading setup:
Symbol: {signal_data['symbol']} | Direction: {signal_data['direction'].upper()}
Pattern: {signal_data['pattern']} | Timeframe: {signal_data['timeframe']}
Entry: {signal_data['entry']:.5f} | Stop: {signal_data['stop']:.5f} | Target: {signal_data['target']:.5f}
R:R: {signal_data.get('rr', 0):.1f}:1

Senior trader: {claude_result.get('narrative', 'N/A')}
HTF aligned: {claude_result.get('htf_aligned', False)}
Strengths: {', '.join(claude_result.get('strengths', []))}
Weaknesses: {', '.join(claude_result.get('weaknesses', []))}"""

        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": prompt}],
            "max_tokens": 150,
            "temperature": 0.1
        }
        async with httpx.AsyncClient() as http:
            res = await http.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=15)
            res.raise_for_status()
            text = res.json()["choices"][0]["message"]["content"].strip()
            result = json.loads(text)
            print(f"[DeepSeek] {signal_data['symbol']}: score={result.get('score', 0)}")
            return result
    except Exception as e:
        print(f"[DeepSeek] Error scoring signal: {e}")
        return {"score": 65, "breakdown": {}}
