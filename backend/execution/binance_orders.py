"""
BLARE Binance Order Execution
Handles crypto order placement via Binance API.
Supports testnet mode — always test before going live.
"""
import hmac
import hashlib
import time
import uuid
import httpx
from urllib.parse import urlencode
from datetime import datetime, timezone
from config.settings import BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_TESTNET
from execution.risk import calculate_position_size, check_daily_limit
from config.firebase import get_db

BASE_URL = "https://testnet.binance.vision" if BINANCE_TESTNET else "https://api.binance.com"


def sign_params(params: dict) -> str:
    query = urlencode(params)
    return hmac.new(BINANCE_API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()


async def get_account_balance(asset: str = "USDT") -> float:
    try:
        params = {"timestamp": int(time.time() * 1000)}
        params["signature"] = sign_params(params)
        headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{BASE_URL}/api/v3/account",
                                   params=params, headers=headers, timeout=10)
            res.raise_for_status()
            balances = {b["asset"]: float(b["free"]) for b in res.json().get("balances", [])}
            return balances.get(asset, 0.0)
    except Exception as e:
        print(f"[Binance] Error fetching balance: {e}")
        return 0.0


async def place_order(signal: dict, profile_id: str = "default") -> dict:
    try:
        symbol = signal["symbol"].replace("/", "")
        direction = signal["direction"]
        side = "BUY" if direction == "long" else "SELL"
        opp_side = "SELL" if direction == "long" else "BUY"

        balance = await get_account_balance("USDT")
        if not await check_daily_limit(balance, profile_id):
            return {"error": "Daily loss limit reached", "executed": False}

        qty = calculate_position_size(balance, signal["position_size_pct"],
                                      signal["entry"], signal["stop"])
        if qty <= 0:
            return {"error": "Invalid position size", "executed": False}

        headers = {"X-MBX-APIKEY": BINANCE_API_KEY}

        entry_params = {"symbol": symbol, "side": side, "type": "MARKET",
                        "quantity": qty, "timestamp": int(time.time() * 1000)}
        entry_params["signature"] = sign_params(entry_params)

        async with httpx.AsyncClient() as client:
            entry_res = await client.post(f"{BASE_URL}/api/v3/order",
                                          params=entry_params, headers=headers, timeout=10)
            entry_res.raise_for_status()
            entry_data = entry_res.json()
            fills = entry_data.get("fills", [{}])
            entry_price = float(fills[0].get("price", signal["entry"])) if fills else signal["entry"]

            oco_params = {
                "symbol": symbol, "side": opp_side, "quantity": qty,
                "price": str(round(signal["target"], 6)),
                "stopPrice": str(round(signal["stop"], 6)),
                "stopLimitPrice": str(round(signal["stop"] * 0.999, 6)),
                "stopLimitTimeInForce": "GTC",
                "timestamp": int(time.time() * 1000)
            }
            oco_params["signature"] = sign_params(oco_params)
            oco_res = await client.post(f"{BASE_URL}/api/v3/order/oco",
                                        params=oco_params, headers=headers, timeout=10)
            oco_res.raise_for_status()

        await _save_trade({
            "signal_id": signal["id"], "profile_id": profile_id,
            "symbol": signal["symbol"], "market": "crypto",
            "direction": direction, "entry": entry_price,
            "stop": signal["stop"], "target": signal["target"],
            "quantity": qty, "status": "open",
            "date": datetime.now(timezone.utc).date().isoformat(),
            "opened_at": datetime.now(timezone.utc).isoformat(),
        })
        print(f"[Binance] Order placed: {symbol} {side} qty:{qty} @ {entry_price}")
        return {"executed": True, "symbol": symbol, "qty": qty, "entry": entry_price}
    except Exception as e:
        print(f"[Binance] Order error: {e}")
        return {"error": str(e), "executed": False}


async def _save_trade(trade_data: dict):
    try:
        get_db().collection("trades").document(str(uuid.uuid4())).set(trade_data)
    except Exception as e:
        print(f"[Binance] Error saving trade: {e}")
