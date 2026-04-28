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


MIN_ORDER_USDT = 15.0  # Binance minimum + safe buffer

# Minimum order quantities per symbol to avoid dust errors
MIN_QTY = {
    "BTCUSDT": 0.00001,
    "ETHUSDT": 0.0001,
    "SOLUSDT": 0.01,
    "DEFAULT": 0.01,
}


def calculate_position_size(account_balance: float, risk_pct: float,
                             entry: float, stop: float) -> float:
    if entry == stop:
        return 0.0
    risk_amount = account_balance * (risk_pct / 100)
    stop_distance_pct = abs(entry - stop) / entry
    quantity = risk_amount / (entry * stop_distance_pct)
    return round(quantity, 6)


def validate_order_size(symbol: str, quantity: float, entry_price: float) -> tuple[bool, str]:
    """Returns (is_valid, reason). Rejects orders below Binance minimums."""
    order_value_usdt = quantity * entry_price
    if order_value_usdt < MIN_ORDER_USDT:
        return False, f"Order value ${order_value_usdt:.2f} below minimum ${MIN_ORDER_USDT}"

    clean_symbol = symbol.replace("/", "")
    min_qty = MIN_QTY.get(clean_symbol, MIN_QTY["DEFAULT"])
    if quantity < min_qty:
        return False, f"Quantity {quantity} below minimum {min_qty} for {clean_symbol}"

    return True, "ok"
