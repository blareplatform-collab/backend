# BLARE — Session 07: Execution Engine

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to build
Prerequisite: Session 06 complete

---

## Context

This session wires live order execution for both crypto (Binance)
and forex/indices/commodities (OANDA). Full auto mode fires trades
immediately on approved signals. Semi-auto mode waits for user approval.
All trades are logged to Firestore.

---

## Goals

- [ ] Binance order execution (market + limit + SL/TP)
- [ ] OANDA order execution (market + limit + SL/TP)
- [ ] Full auto mode — fires on signal creation
- [ ] Semi-auto mode — fires on user approve tap
- [ ] Daily loss limit check before every order
- [ ] All trades saved to Firestore
- [ ] Open positions tracked
- [ ] POST /signals/{id}/approve triggers execution

---

## Step 1 — Risk manager

### backend/execution/risk.py
```python
"""
BLARE Risk Manager
Checks daily loss limits and calculates order sizes before execution.
All execution must pass through here first.
"""
from datetime import datetime, timezone
from config.settings import MAX_DAILY_LOSS_PCT
from config.firebase import get_db

async def get_daily_pnl(profile_id: str = "default") -> float:
    """Calculate today's P&L from Firestore trade history."""
    try:
        db = get_db()
        today = datetime.now(timezone.utc).date().isoformat()
        docs = (db.collection("trades")
                  .where("profile_id", "==", profile_id)
                  .where("date", "==", today)
                  .stream())
        trades = [doc.to_dict() for doc in docs]
        return sum(t.get("pnl", 0) for t in trades)
    except Exception as e:
        print(f"[Risk] Error fetching daily P&L: {e}")
        return 0.0

async def check_daily_limit(account_balance: float,
                             profile_id: str = "default") -> bool:
    """
    Returns True if trading is allowed (daily loss limit not breached).
    Returns False if max daily loss reached — halt all trading.
    """
    daily_pnl = await get_daily_pnl(profile_id)
    max_loss = account_balance * (MAX_DAILY_LOSS_PCT / 100)

    if daily_pnl <= -max_loss:
        print(f"[Risk] DAILY LOSS LIMIT REACHED: {daily_pnl:.2f} "
              f"/ -{max_loss:.2f}. Trading halted.")
        return False
    return True

def calculate_position_size(account_balance: float, risk_pct: float,
                             entry: float, stop: float) -> float:
    """
    Calculate position size in base units.
    risk_pct = percentage of account to risk (e.g. 1.0 for 1%)
    Returns quantity to trade.
    """
    if entry == stop:
        return 0.0
    risk_amount = account_balance * (risk_pct / 100)
    stop_distance = abs(entry - stop)
    stop_distance_pct = stop_distance / entry
    quantity = risk_amount / (entry * stop_distance_pct)
    return round(quantity, 6)
```

---

## Step 2 — Binance execution

### backend/execution/binance_orders.py
```python
"""
BLARE Binance Order Execution
Handles crypto order placement via Binance API.
Supports testnet mode — always test before going live.
"""
import httpx
import hmac
import hashlib
import time
from urllib.parse import urlencode
from config.settings import BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_TESTNET
from execution.risk import calculate_position_size, check_daily_limit
from config.firebase import get_db
from datetime import datetime, timezone

BASE_URL = ("https://testnet.binance.vision"
            if BINANCE_TESTNET else "https://api.binance.com")

def sign_params(params: dict) -> str:
    """Generate HMAC-SHA256 signature for Binance request."""
    query = urlencode(params)
    return hmac.new(
        BINANCE_API_SECRET.encode(), query.encode(), hashlib.sha256
    ).hexdigest()

async def get_account_balance(asset: str = "USDT") -> float:
    """Fetch available balance for an asset."""
    try:
        params = {"timestamp": int(time.time() * 1000)}
        params["signature"] = sign_params(params)
        headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{BASE_URL}/api/v3/account",
                params=params, headers=headers, timeout=10
            )
            res.raise_for_status()
            data = res.json()
            balances = {b["asset"]: float(b["free"])
                        for b in data.get("balances", [])}
            return balances.get(asset, 0.0)
    except Exception as e:
        print(f"[Binance] Error fetching balance: {e}")
        return 0.0

async def place_order(signal: dict, profile_id: str = "default") -> dict:
    """
    Place a market order with OCO (stop loss + take profit) on Binance.
    Returns order result dict.
    """
    try:
        symbol = signal["symbol"].replace("/", "")
        direction = signal["direction"]
        side = "BUY" if direction == "long" else "SELL"
        opp_side = "SELL" if direction == "long" else "BUY"

        # Get balance and check daily limit
        balance = await get_account_balance("USDT")
        allowed = await check_daily_limit(balance, profile_id)
        if not allowed:
            return {"error": "Daily loss limit reached", "executed": False}

        # Calculate quantity
        qty = calculate_position_size(
            balance, signal["position_size_pct"],
            signal["entry"], signal["stop"]
        )
        if qty <= 0:
            return {"error": "Invalid position size", "executed": False}

        headers = {"X-MBX-APIKEY": BINANCE_API_KEY}

        # 1. Place market entry order
        entry_params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": qty,
            "timestamp": int(time.time() * 1000)
        }
        entry_params["signature"] = sign_params(entry_params)

        async with httpx.AsyncClient() as client:
            entry_res = await client.post(
                f"{BASE_URL}/api/v3/order",
                params=entry_params, headers=headers, timeout=10
            )
            entry_res.raise_for_status()
            entry_data = entry_res.json()
            entry_price = float(entry_data.get("fills", [{}])[0].get("price",
                                                                       signal["entry"]))

            # 2. Place OCO (stop loss + take profit)
            oco_params = {
                "symbol": symbol,
                "side": opp_side,
                "quantity": qty,
                "price": str(round(signal["target"], 6)),
                "stopPrice": str(round(signal["stop"], 6)),
                "stopLimitPrice": str(round(signal["stop"] * 0.999, 6)),
                "stopLimitTimeInForce": "GTC",
                "timestamp": int(time.time() * 1000)
            }
            oco_params["signature"] = sign_params(oco_params)
            oco_res = await client.post(
                f"{BASE_URL}/api/v3/order/oco",
                params=oco_params, headers=headers, timeout=10
            )
            oco_res.raise_for_status()

        # Save trade to Firestore
        await save_trade({
            "signal_id": signal["id"],
            "profile_id": profile_id,
            "symbol": signal["symbol"],
            "market": "crypto",
            "direction": direction,
            "entry": entry_price,
            "stop": signal["stop"],
            "target": signal["target"],
            "quantity": qty,
            "status": "open",
            "date": datetime.now(timezone.utc).date().isoformat(),
            "opened_at": datetime.now(timezone.utc).isoformat(),
        })

        print(f"[Binance] Order placed: {symbol} {side} qty:{qty} @ {entry_price}")
        return {"executed": True, "symbol": symbol, "qty": qty, "entry": entry_price}

    except Exception as e:
        print(f"[Binance] Order error: {e}")
        return {"error": str(e), "executed": False}

async def save_trade(trade_data: dict):
    """Save trade record to Firestore."""
    try:
        import uuid
        db = get_db()
        trade_id = str(uuid.uuid4())
        db.collection("trades").document(trade_id).set(trade_data)
    except Exception as e:
        print(f"[Binance] Error saving trade: {e}")
```

---

## Step 3 — OANDA execution

### backend/execution/oanda_orders.py
```python
"""
BLARE OANDA Order Execution
Handles forex/indices/commodities order placement via OANDA v20 API.
Use practice account for all testing.
"""
import httpx
from config.settings import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_ENVIRONMENT
from execution.risk import calculate_position_size, check_daily_limit
from config.firebase import get_db
from datetime import datetime, timezone
import uuid

BASE_URL = (
    "https://api-fxpractice.oanda.com"
    if OANDA_ENVIRONMENT == "practice"
    else "https://api-fxtrade.oanda.com"
)

HEADERS = {
    "Authorization": f"Bearer {OANDA_API_KEY}",
    "Content-Type": "application/json"
}

async def get_account_balance() -> float:
    """Fetch OANDA account balance."""
    try:
        url = f"{BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/summary"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            data = res.json()
            return float(data["account"]["balance"])
    except Exception as e:
        print(f"[OANDA] Error fetching balance: {e}")
        return 0.0

async def place_order(signal: dict, profile_id: str = "default") -> dict:
    """
    Place a market order with SL/TP on OANDA.
    Units are negative for short positions.
    """
    try:
        instrument = signal["symbol"].replace("/", "_")
        direction = signal["direction"]

        balance = await get_account_balance()
        allowed = await check_daily_limit(balance, profile_id)
        if not allowed:
            return {"error": "Daily loss limit reached", "executed": False}

        qty = calculate_position_size(
            balance, signal["position_size_pct"],
            signal["entry"], signal["stop"]
        )
        units = int(qty * 1000)  # OANDA uses units (e.g. 1000 = 1 micro lot)
        if direction == "short":
            units = -units

        payload = {
            "order": {
                "type": "MARKET",
                "instrument": instrument,
                "units": str(units),
                "stopLossOnFill": {
                    "price": str(round(signal["stop"], 5))
                },
                "takeProfitOnFill": {
                    "price": str(round(signal["target"], 5))
                },
                "timeInForce": "FOK"
            }
        }

        url = f"{BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/orders"
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=HEADERS,
                                    json=payload, timeout=10)
            res.raise_for_status()
            data = res.json()

        # Save trade
        await _save_trade({
            "signal_id": signal["id"],
            "profile_id": profile_id,
            "symbol": signal["symbol"],
            "market": signal["market"],
            "direction": direction,
            "entry": signal["entry"],
            "stop": signal["stop"],
            "target": signal["target"],
            "units": units,
            "status": "open",
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
        db = get_db()
        db.collection("trades").document(str(uuid.uuid4())).set(trade_data)
    except Exception as e:
        print(f"[OANDA] Error saving trade: {e}")
```

---

## Step 4 — Execution router

### backend/execution/router.py
```python
"""
BLARE Execution Router
Routes signal execution to correct connector based on market.
Handles full auto and semi-auto modes.
"""
from execution.binance_orders import place_order as binance_order
from execution.oanda_orders import place_order as oanda_order

CRYPTO_MARKETS = {"crypto"}
OANDA_MARKETS = {"forex", "indices", "commodities"}

async def execute_signal(signal_data: dict,
                          profile_id: str = "default") -> dict:
    """Route execution to the correct connector."""
    market = signal_data.get("market", "")
    if market in CRYPTO_MARKETS:
        return await binance_order(signal_data, profile_id)
    elif market in OANDA_MARKETS:
        return await oanda_order(signal_data, profile_id)
    else:
        return {"error": f"Unknown market: {market}", "executed": False}
```

---

## Step 5 — Update signals route for approve/execute

Update `backend/routes/signals.py` approve endpoint:

```python
from execution.router import execute_signal
from config.settings import AUTO_TRADE_MODE  # add to settings.py

@router.post("/{signal_id}/approve")
async def approve_signal(signal_id: str, profile_id: str = "default"):
    """Approve + execute a signal (semi-auto mode)."""
    try:
        db = get_db()
        doc = db.collection("signals").document(signal_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Signal not found")

        signal_data = doc.to_dict()
        result = await execute_signal(signal_data, profile_id)

        new_status = "executed" if result.get("executed") else "failed"
        db.collection("signals").document(signal_id).update({
            "status": new_status,
            "execution_result": result
        })
        return {"status": new_status, "execution": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Add to `backend/config/settings.py`:
```python
AUTO_TRADE_MODE = os.getenv("AUTO_TRADE_MODE", "semi").lower()
# "semi" = wait for user approval
# "auto" = execute immediately
```

Update scanner to auto-execute if in auto mode:
```python
from config.settings import AUTO_TRADE_MODE
from execution.router import execute_signal

if enriched:
    _recent_signals[dedup_key] = now
    await save_signal(enriched)
    if AUTO_TRADE_MODE == "auto":
        await execute_signal(enriched.to_dict())
```

---

## Step 6 — Trades route

### backend/routes/trades.py
```python
"""BLARE trades route."""
from fastapi import APIRouter, Query
from config.firebase import get_db

router = APIRouter()

@router.get("/")
async def get_trades(limit: int = Query(default=20, le=100)):
    """Get trade history."""
    try:
        db = get_db()
        docs = (db.collection("trades")
                  .order_by("opened_at", direction="DESCENDING")
                  .limit(limit).stream())
        return {"trades": [doc.to_dict() for doc in docs]}
    except Exception as e:
        return {"error": str(e), "trades": []}

@router.get("/open")
async def get_open_positions():
    """Get all open positions."""
    try:
        db = get_db()
        docs = (db.collection("trades")
                  .where("status", "==", "open").stream())
        return {"positions": [doc.to_dict() for doc in docs]}
    except Exception as e:
        return {"error": str(e), "positions": []}
```

---

## Step 7 — Verify (TESTNET / PRACTICE ONLY)

```bash
# Confirm BINANCE_TESTNET=true and OANDA_ENVIRONMENT=practice in .env

# Manually approve a signal
curl -X POST http://localhost:8000/signals/{signal_id}/approve

# Check trade was saved
curl http://localhost:8000/trades/open
```

Checklist:
- [ ] Binance testnet orders placing correctly
- [ ] OANDA practice orders placing correctly
- [ ] Daily loss limit halts trading when breached
- [ ] Semi-auto approve endpoint triggers execution
- [ ] Auto mode fires on signal creation when enabled
- [ ] All trades saved to Firestore with correct data
- [ ] Never tested on live accounts until fully verified

---

## Session 07 Complete

Commit message: `feat: session 07 — execution engine complete`

Next: **Session 08 — Dashboard UI**
