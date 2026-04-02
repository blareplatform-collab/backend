"""
BLARE Execution Router
Routes signal execution to correct connector based on market.
"""
from execution.binance_orders import place_order as binance_order
from execution.oanda_orders import place_order as oanda_order

CRYPTO_MARKETS = {"crypto"}
OANDA_MARKETS = {"forex", "indices", "commodities"}


async def execute_signal(signal_data: dict, profile_id: str = "default") -> dict:
    market = signal_data.get("market", "")
    if market in CRYPTO_MARKETS:
        return await binance_order(signal_data, profile_id)
    elif market in OANDA_MARKETS:
        return await oanda_order(signal_data, profile_id)
    else:
        return {"error": f"Unknown market: {market}", "executed": False}
