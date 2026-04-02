"""
BLARE OANDA Order Execution
Handles forex/indices/commodities order placement via OANDA v20 API.
Use practice account for all testing.
"""
import uuid
import httpx
from datetime import datetime, timezone
from config.settings import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_ENVIRONMENT
from execution.risk import calculate_position_size, check_daily_limit
from config.firebase import get_db

BASE_URL = (
    "https://api-fxpractice.oanda.com"
    if OANDA_ENVIRONMENT == "practice"
    else "https://api-fxtrade.oanda.com"
)
HEADERS = {"Authorization": f"Bearer {OANDA_API_KEY}", "Content-Type": "application/json"}


async def get_account_balance() -> float:
    try:
        url = f"{BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/summary"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            return float(res.json()["account"]["balance"])
    except Exception as e:
        print(f"[OANDA] Error fetching balance: {e}")
        return 0.0


async def place_order(signal: dict, profile_id: str = "default") -> dict:
    try:
        instrument = signal["symbol"].replace("/", "_")
        direction = signal["direction"]

        balance = await get_account_balance()
        if not await check_daily_limit(balance, profile_id):
            return {"error": "Daily loss limit reached", "executed": False}

        qty = calculate_position_size(balance, signal["position_size_pct"],
                                      signal["entry"], signal["stop"])
        units = int(qty * 1000)
        if direction == "short":
            units = -units

        payload = {
            "order": {
                "type": "MARKET",
                "instrument": instrument,
                "units": str(units),
                "stopLossOnFill": {"price": str(round(signal["stop"], 5))},
                "takeProfitOnFill": {"price": str(round(signal["target"], 5))},
                "timeInForce": "FOK"
            }
        }
        url = f"{BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/orders"
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=HEADERS, json=payload, timeout=10)
            res.raise_for_status()

        await _save_trade({
            "signal_id": signal["id"], "profile_id": profile_id,
            "symbol": signal["symbol"], "market": signal["market"],
            "direction": direction, "entry": signal["entry"],
            "stop": signal["stop"], "target": signal["target"],
            "units": units, "status": "open",
            "date": datetime.now(timezone.utc).date().isoformat(),
            "opened_at": datetime.now(timezone.utc).isoformat(),
        })
        print(f"[OANDA] Order placed: {instrument} {direction} units:{units}")
        return {"executed": True, "symbol": signal["symbol"], "units": units}
    except Exception as e:
        print(f"[OANDA] Order error: {e}")
        return {"error": str(e), "executed": False}


async def _save_trade(trade_data: dict):
    try:
        get_db().collection("trades").document(str(uuid.uuid4())).set(trade_data)
    except Exception as e:
        print(f"[OANDA] Error saving trade: {e}")
