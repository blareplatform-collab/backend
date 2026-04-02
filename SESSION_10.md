# BLARE — Session 10: Backtest + Analytics

Version: 1.0.0
Last updated: 2026-03-29
Status: Ready to build
Prerequisite: Session 09 complete

---

## Context

The final session. This builds the backtesting engine and full analytics
dashboard. After this session BLARE is complete — every strategy can be
tested on historical data, and every performance metric is tracked and visualized.

---

## Goals

- [ ] Backtesting engine — run any strategy on historical data
- [ ] Backtest results: win rate, avg R:R, max drawdown, equity curve
- [ ] POST /backtest endpoint
- [ ] Backtest UI — select strategy + market + date range + run
- [ ] Analytics page — win rate per strategy, avg R:R, drawdown, confidence accuracy
- [ ] All analytics persisted in Firestore
- [ ] Equity curve chart (TradingView Lightweight Charts)

---

## Step 1 — Backtesting engine

### backend/engine/backtest.py
```python
"""
BLARE Backtesting Engine
Runs any loaded strategy against historical OHLCV data.
Returns performance metrics and full trade log.

Process:
  1. Fetch historical candles for symbol + timeframe + date range
  2. Walk through candles chronologically (no lookahead)
  3. On each candle, run pattern detection
  4. Simulate entry, stop, and target execution
  5. Calculate performance metrics
"""
from typing import Optional
from engine.loader import get_strategy
from engine.patterns.smc import detect_all as detect_smc
from engine.patterns.wyckoff import detect_wyckoff
from engine.patterns.classic_ta import detect_all as detect_classic
from connectors.unified import get_candles
import math

def simulate_trade(candles: list, signal: dict,
                   start_idx: int) -> dict:
    """
    Simulate a trade from entry index forward.
    Walk candles until stop or target is hit.
    Returns trade result dict.
    """
    entry = signal["entry"]
    stop = signal["stop"]
    target = signal["target"]
    direction = signal["direction"]

    result = {
        "entry": entry,
        "stop": stop,
        "target": target,
        "direction": direction,
        "outcome": "open",
        "exit_price": None,
        "pnl_r": 0,  # profit/loss in R multiples
        "bars_held": 0,
    }

    for i in range(start_idx, min(start_idx + 200, len(candles))):
        c = candles[i]
        result["bars_held"] = i - start_idx

        if direction == "long":
            if c["low"] <= stop:  # stopped out
                result["outcome"] = "loss"
                result["exit_price"] = stop
                result["pnl_r"] = -1.0
                break
            if c["high"] >= target:  # target hit
                result["outcome"] = "win"
                result["exit_price"] = target
                rr = abs(target - entry) / abs(entry - stop)
                result["pnl_r"] = round(rr, 2)
                break
        else:  # short
            if c["high"] >= stop:
                result["outcome"] = "loss"
                result["exit_price"] = stop
                result["pnl_r"] = -1.0
                break
            if c["low"] <= target:
                result["outcome"] = "win"
                result["exit_price"] = target
                rr = abs(entry - target) / abs(stop - entry)
                result["pnl_r"] = round(rr, 2)
                break

    if result["outcome"] == "open":
        result["outcome"] = "timeout"
        result["exit_price"] = candles[min(start_idx + 199,
                                           len(candles) - 1)]["close"]
        result["pnl_r"] = 0

    return result

def calculate_metrics(trades: list, initial_balance: float = 10000) -> dict:
    """
    Calculate performance metrics from a list of simulated trades.
    Returns comprehensive stats dict.
    """
    if not trades:
        return {}

    wins = [t for t in trades if t["outcome"] == "win"]
    losses = [t for t in trades if t["outcome"] == "loss"]
    total = len(trades)

    win_rate = len(wins) / total * 100 if total > 0 else 0
    avg_rr = sum(t["pnl_r"] for t in wins) / len(wins) if wins else 0

    # Equity curve (1% risk per trade)
    balance = initial_balance
    equity_curve = [balance]
    peak = balance
    max_drawdown = 0

    for trade in trades:
        risk_amount = balance * 0.01
        pnl = risk_amount * trade["pnl_r"]
        balance += pnl
        equity_curve.append(round(balance, 2))
        if balance > peak:
            peak = balance
        dd = (peak - balance) / peak * 100
        if dd > max_drawdown:
            max_drawdown = dd

    total_return = ((balance - initial_balance) / initial_balance) * 100
    profit_factor = (
        sum(t["pnl_r"] for t in wins) /
        abs(sum(t["pnl_r"] for t in losses))
        if losses else 999
    )

    return {
        "total_trades": total,
        "wins": len(wins),
        "losses": len(losses),
        "timeouts": len([t for t in trades if t["outcome"] == "timeout"]),
        "win_rate": round(win_rate, 1),
        "avg_rr": round(avg_rr, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "profit_factor": round(profit_factor, 2),
        "total_return_pct": round(total_return, 2),
        "final_balance": round(balance, 2),
        "equity_curve": equity_curve,
    }

async def run_backtest(strategy_id: str, symbol: str,
                       timeframe: str, limit: int = 500) -> dict:
    """
    Run a full backtest for a strategy on a symbol.

    Steps:
    1. Load historical candles
    2. Walk through chronologically
    3. Detect patterns at each step
    4. Simulate each trade
    5. Return metrics + trade log
    """
    strategy = get_strategy(strategy_id)
    if not strategy:
        return {"error": f"Strategy not found: {strategy_id}"}

    candles = get_candles(symbol, timeframe, limit=limit)
    if len(candles) < 100:
        return {"error": "Not enough historical data"}

    print(f"[Backtest] Running {strategy_id} on {symbol} {timeframe} "
          f"— {len(candles)} candles")

    trades = []
    min_candles = 60  # minimum candles needed for detection

    i = min_candles
    while i < len(candles) - 5:
        window = candles[:i]

        # Try all detector families
        result = None
        for detector in [
            lambda c, s: detect_smc(c, s, timeframe),
            lambda c, s: detect_wyckoff(c, s),
            lambda c, s: detect_classic(c, s),
        ]:
            result = detector(window, strategy)
            if result:
                break

        if result:
            # Check R:R minimum
            if result["entry"] != result["stop"]:
                rr = abs(result["target"] - result["entry"]) / \
                     abs(result["entry"] - result["stop"])
                if rr >= strategy.get("min_rr", 2.0):
                    trade = simulate_trade(candles, result, i)
                    trade.update({
                        "symbol": symbol,
                        "strategy": strategy_id,
                        "timeframe": timeframe,
                        "candle_idx": i,
                        "timestamp": candles[i]["timestamp"],
                    })
                    trades.append(trade)
                    i += 20  # skip ahead after signal to avoid overlapping trades
                    continue

        i += 1

    metrics = calculate_metrics(trades)
    print(f"[Backtest] Complete: {metrics.get('total_trades', 0)} trades, "
          f"WR:{metrics.get('win_rate', 0)}% RR:{metrics.get('avg_rr', 0)}")

    return {
        "strategy": strategy_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "candles_analyzed": len(candles),
        "metrics": metrics,
        "trades": trades,
    }
```

---

## Step 2 — Backtest route

### backend/routes/backtest.py
```python
"""BLARE backtest route."""
from fastapi import APIRouter
from pydantic import BaseModel
from engine.backtest import run_backtest
from config.firebase import get_db
from datetime import datetime, timezone

router = APIRouter()

class BacktestRequest(BaseModel):
    strategy_id: str
    symbol: str
    timeframe: str = "4h"
    limit: int = 500

@router.post("/")
async def run_backtest_endpoint(req: BacktestRequest):
    """Run a backtest for a strategy on a symbol."""
    result = await run_backtest(
        req.strategy_id, req.symbol, req.timeframe, req.limit
    )

    # Save backtest result to Firestore
    if "metrics" in result:
        try:
            db = get_db()
            import uuid
            db.collection("backtests").document(str(uuid.uuid4())).set({
                **result,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "equity_curve": result["metrics"].get("equity_curve", []),
            })
        except Exception as e:
            print(f"[Backtest] Error saving to Firestore: {e}")

    return result

@router.get("/history")
async def get_backtest_history(limit: int = 20):
    """Get recent backtest results."""
    try:
        db = get_db()
        docs = (db.collection("backtests")
                  .order_by("created_at", direction="DESCENDING")
                  .limit(limit).stream())
        return {"backtests": [doc.to_dict() for doc in docs]}
    except Exception as e:
        return {"error": str(e), "backtests": []}
```

---

## Step 3 — Analytics route

### backend/routes/analytics.py
```python
"""BLARE analytics route."""
from fastapi import APIRouter
from config.firebase import get_db

router = APIRouter()

@router.get("/summary")
async def get_analytics_summary():
    """Get overall trading performance summary."""
    try:
        db = get_db()
        trades = [doc.to_dict() for doc in db.collection("trades").stream()]
        signals = [doc.to_dict() for doc in
                   db.collection("signals")
                     .where("status", "in", ["executed", "rejected"]).stream()]

        if not trades:
            return {"message": "No trades yet"}

        closed = [t for t in trades if t.get("pnl") is not None]
        wins = [t for t in closed if t.get("pnl", 0) > 0]
        losses = [t for t in closed if t.get("pnl", 0) < 0]

        # Win rate per strategy
        strategy_stats = {}
        for t in closed:
            sid = t.get("strategy", "unknown")
            if sid not in strategy_stats:
                strategy_stats[sid] = {"wins": 0, "losses": 0, "total_rr": 0}
            if t.get("pnl", 0) > 0:
                strategy_stats[sid]["wins"] += 1
            else:
                strategy_stats[sid]["losses"] += 1

        # AI confidence accuracy
        high_conf = [s for s in signals if s.get("confidence", 0) >= 70
                     and s.get("status") == "executed"]
        low_conf = [s for s in signals if s.get("confidence", 0) < 70
                    and s.get("status") == "executed"]

        return {
            "total_trades": len(closed),
            "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else 0,
            "total_pnl": round(sum(t.get("pnl", 0) for t in closed), 2),
            "strategy_stats": strategy_stats,
            "high_conf_signals": len(high_conf),
            "low_conf_signals": len(low_conf),
        }
    except Exception as e:
        return {"error": str(e)}
```

Add to `main.py`:
```python
from routes import analytics
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
```

---

## Step 4 — Backtest UI

### frontend/src/pages/Backtest.jsx
```jsx
import { useState } from "react"
import { useSignalStore } from "../store/signalStore"
import api from "../utils/api"
import { createChart } from "lightweight-charts"
import { useEffect, useRef } from "react"

const STRATEGIES = ["smc_fvg_entry", "smc_liquidity_sweep",
                    "smc_order_block", "wyckoff_spring"]
const SYMBOLS = ["BTC/USDT", "ETH/USDT", "EUR/USD", "GBP/USD", "SPX"]
const TIMEFRAMES = ["15m", "1h", "4h", "1d"]

export default function Backtest() {
  const [form, setForm] = useState({
    strategy_id: STRATEGIES[0], symbol: SYMBOLS[0], timeframe: "4h"
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  const runBacktest = async () => {
    setLoading(true)
    try {
      const data = await api.post("/backtest", form)
      setResult(data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => {
    if (!result?.metrics?.equity_curve || !chartRef.current) return
    if (chartInstance.current) chartInstance.current.remove()

    const chart = createChart(chartRef.current, {
      layout: { background: { color: "#0d1f1b" }, textColor: "#6b7280" },
      grid: { vertLines: { color: "#142b26" }, horzLines: { color: "#142b26" } },
      height: 250,
    })
    chartInstance.current = chart

    const series = chart.addLineSeries({ color: "#1D9E75", lineWidth: 2 })
    const data = result.metrics.equity_curve.map((v, i) => ({ time: i, value: v }))
    series.setData(data)
    chart.timeScale().fitContent()
  }, [result])

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-white text-xl font-medium mb-6">Backtest</h1>

      {/* Form */}
      <div className="bg-dark-800 rounded-xl p-5 mb-6 grid grid-cols-2 gap-4">
        {[
          { label: "Strategy", key: "strategy_id", options: STRATEGIES },
          { label: "Symbol", key: "symbol", options: SYMBOLS },
          { label: "Timeframe", key: "timeframe", options: TIMEFRAMES },
        ].map(({ label, key, options }) => (
          <div key={key}>
            <label className="text-gray-500 text-xs mb-1 block">{label}</label>
            <select
              value={form[key]}
              onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
              className="w-full bg-dark-900 text-white text-sm rounded-lg
                         border border-dark-700 px-3 py-2 outline-none
                         focus:border-teal-600">
              {options.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
        ))}

        <div className="col-span-2">
          <button
            onClick={runBacktest}
            disabled={loading}
            className="w-full bg-teal-600 hover:bg-teal-500 disabled:opacity-50
                       text-white rounded-lg py-2.5 text-sm font-medium transition-colors">
            {loading ? "Running backtest..." : "Run backtest"}
          </button>
        </div>
      </div>

      {/* Results */}
      {result?.metrics && (
        <>
          {/* Stats grid */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            {[
              { label: "Total trades", value: result.metrics.total_trades },
              { label: "Win rate", value: `${result.metrics.win_rate}%` },
              { label: "Avg R:R", value: `${result.metrics.avg_rr}:1` },
              { label: "Max drawdown", value: `${result.metrics.max_drawdown_pct}%` },
              { label: "Profit factor", value: result.metrics.profit_factor },
              { label: "Total return", value: `${result.metrics.total_return_pct}%` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-dark-800 rounded-xl p-4 text-center">
                <div className="text-gray-500 text-xs mb-1">{label}</div>
                <div className="text-white font-medium text-lg">{value}</div>
              </div>
            ))}
          </div>

          {/* Equity curve */}
          <div className="bg-dark-800 rounded-xl p-4 mb-6">
            <div className="text-gray-500 text-xs mb-3">Equity curve</div>
            <div ref={chartRef} />
          </div>

          {/* Trade log */}
          <div className="bg-dark-800 rounded-xl p-4">
            <div className="text-gray-500 text-xs mb-3">
              Trade log ({result.trades?.length} trades)
            </div>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {result.trades?.map((t, i) => (
                <div key={i} className="flex justify-between text-xs py-1
                                        border-b border-dark-700">
                  <span className="text-gray-400">{t.direction?.toUpperCase()}</span>
                  <span className={t.outcome === "win"
                    ? "text-teal-400" : "text-red-400"}>
                    {t.outcome} {t.pnl_r > 0 ? `+${t.pnl_r}R` : `${t.pnl_r}R`}
                  </span>
                  <span className="text-gray-600">{t.bars_held} bars</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
```

---

## Step 5 — Analytics page

### frontend/src/pages/Analytics.jsx
```jsx
import { useEffect, useState } from "react"
import api from "../utils/api"

export default function Analytics() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api.get("/analytics/summary").then(setStats).catch(console.error)
  }, [])

  if (!stats) return (
    <div className="p-6 text-gray-600 text-center">Loading analytics...</div>
  )

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-white text-xl font-medium mb-6">Analytics</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {[
          { label: "Total trades", value: stats.total_trades },
          { label: "Win rate", value: `${stats.win_rate}%` },
          { label: "Total P&L", value: `$${stats.total_pnl}` },
          { label: "High conf signals", value: stats.high_conf_signals },
        ].map(({ label, value }) => (
          <div key={label} className="bg-dark-800 rounded-xl p-5">
            <div className="text-gray-500 text-xs mb-1">{label}</div>
            <div className="text-white text-2xl font-medium">{value}</div>
          </div>
        ))}
      </div>

      {/* Strategy breakdown */}
      {stats.strategy_stats && Object.keys(stats.strategy_stats).length > 0 && (
        <div className="bg-dark-800 rounded-xl p-4">
          <div className="text-gray-500 text-xs mb-3">Win rate per strategy</div>
          {Object.entries(stats.strategy_stats).map(([sid, s]) => {
            const total = s.wins + s.losses
            const wr = total > 0 ? Math.round(s.wins / total * 100) : 0
            return (
              <div key={sid} className="flex items-center gap-3 py-2
                                        border-b border-dark-700">
                <span className="text-gray-400 text-sm flex-1">{sid}</span>
                <div className="flex-1 bg-dark-900 rounded-full h-1.5">
                  <div className="bg-teal-400 h-1.5 rounded-full"
                       style={{ width: `${wr}%` }} />
                </div>
                <span className="text-teal-400 text-sm w-10 text-right">
                  {wr}%
                </span>
              </div>
            )
          })}
        </div>
      )}

      {!stats.total_trades && (
        <div className="text-center text-gray-600 py-12">
          No trades yet — run some backtests or let BLARE trade live.
        </div>
      )}
    </div>
  )
}
```

---

## Step 6 — Final verification

```bash
# Run a backtest
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": "smc_fvg_entry", "symbol": "BTC/USDT", "timeframe": "4h"}'

# Get analytics
curl http://localhost:8000/analytics/summary

# Check backtest history
curl http://localhost:8000/backtest/history
```

Full system checklist — everything from Session 01 to 10:
- [ ] Backend running on Railway
- [ ] Firebase connected (Auth + Firestore)
- [ ] Live data flowing (Binance + OANDA + Alpha Vantage)
- [ ] Pattern engine scanning every 30s
- [ ] SMC + Wyckoff + Classic TA all detecting
- [ ] AI validation on every signal
- [ ] Execution working on testnet/practice
- [ ] Desktop app boots with splash
- [ ] Web app deployed on Firebase Hosting
- [ ] Mobile app running on device
- [ ] Backtest engine returning results
- [ ] Analytics dashboard showing stats
- [ ] All API keys in .env only — nothing hardcoded
- [ ] Git repo clean with session-by-session commit history

---

## Session 10 Complete — BLARE v1.0 DONE

Commit message: `feat: session 10 — backtest + analytics complete. BLARE v1.0 🚀`

---

*BLARE — when the market speaks, BLARE is louder.*
