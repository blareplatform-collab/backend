"""
BLARE Risk Manager
Checks daily loss limits and calculates order sizes before execution.
"""
from datetime import datetime, timezone
from config.settings import MAX_DAILY_LOSS_PCT
from config.firebase import get_db


async def get_daily_pnl(profile_id: str = "default") -> float:
    try:
        db = get_db()
        today = datetime.now(timezone.utc).date().isoformat()
        docs = (db.collection("trades")
                  .where("profile_id", "==", profile_id)
                  .where("date", "==", today)
                  .stream())
        return sum(t.to_dict().get("pnl", 0) for t in docs)
    except Exception as e:
        print(f"[Risk] Error fetching daily P&L: {e}")
        return 0.0


async def check_daily_limit(account_balance: float, profile_id: str = "default") -> bool:
    daily_pnl = await get_daily_pnl(profile_id)
    max_loss = account_balance * (MAX_DAILY_LOSS_PCT / 100)
    if daily_pnl <= -max_loss:
        print(f"[Risk] DAILY LOSS LIMIT REACHED: {daily_pnl:.2f} / -{max_loss:.2f}. Trading halted.")
        return False
    return True


def calculate_position_size(account_balance: float, risk_pct: float,
                             entry: float, stop: float) -> float:
    if entry == stop:
        return 0.0
    risk_amount = account_balance * (risk_pct / 100)
    stop_distance_pct = abs(entry - stop) / entry
    quantity = risk_amount / (entry * stop_distance_pct)
    return round(quantity, 6)
