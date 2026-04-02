"""
BLARE Backtesting Engine
Runs any loaded strategy against historical OHLCV data.
Returns performance metrics and full trade log.
"""
from engine.loader import get_strategy
from engine.patterns.smc import detect_all as detect_smc
from engine.patterns.wyckoff import detect_wyckoff
from engine.patterns.classic_ta import detect_all as detect_classic
from connectors.unified import get_candles


def simulate_trade(candles: list, signal: dict, start_idx: int) -> dict:
    """Walk candles from entry index until stop or target is hit."""
    entry = signal["entry"]
    stop = signal["stop"]
    target = signal["target"]
    direction = signal["direction"]

    result = {
        "entry": entry, "stop": stop, "target": target,
        "direction": direction, "outcome": "open",
        "exit_price": None, "pnl_r": 0, "bars_held": 0,
    }

    for i in range(start_idx, min(start_idx + 200, len(candles))):
        c = candles[i]
        result["bars_held"] = i - start_idx

        if direction == "long":
            if c["low"] <= stop:
                result.update({"outcome": "loss", "exit_price": stop, "pnl_r": -1.0})
                return result
            if c["high"] >= target:
                rr = abs(target - entry) / abs(entry - stop)
                result.update({"outcome": "win", "exit_price": target, "pnl_r": round(rr, 2)})
                return result
        else:
            if c["high"] >= stop:
                result.update({"outcome": "loss", "exit_price": stop, "pnl_r": -1.0})
                return result
            if c["low"] <= target:
                rr = abs(entry - target) / abs(stop - entry)
                result.update({"outcome": "win", "exit_price": target, "pnl_r": round(rr, 2)})
                return result

    result["outcome"] = "timeout"
    result["exit_price"] = candles[min(start_idx + 199, len(candles) - 1)]["close"]
    return result


def calculate_metrics(trades: list, initial_balance: float = 10000) -> dict:
    """Calculate performance metrics from simulated trade list."""
    if not trades:
        return {}

    wins = [t for t in trades if t["outcome"] == "win"]
    losses = [t for t in trades if t["outcome"] == "loss"]
    total = len(trades)

    win_rate = len(wins) / total * 100 if total else 0
    avg_rr = sum(t["pnl_r"] for t in wins) / len(wins) if wins else 0

    balance = initial_balance
    equity_curve = [balance]
    peak = balance
    max_drawdown = 0

    for trade in trades:
        risk_amount = balance * 0.01
        balance += risk_amount * trade["pnl_r"]
        equity_curve.append(round(balance, 2))
        if balance > peak:
            peak = balance
        dd = (peak - balance) / peak * 100
        if dd > max_drawdown:
            max_drawdown = dd

    total_return = ((balance - initial_balance) / initial_balance) * 100
    loss_r = abs(sum(t["pnl_r"] for t in losses))
    profit_factor = sum(t["pnl_r"] for t in wins) / loss_r if loss_r else 999

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
    strategy = get_strategy(strategy_id)
    if not strategy:
        return {"error": f"Strategy not found: {strategy_id}"}

    candles = get_candles(symbol, timeframe, limit=limit)
    if len(candles) < 100:
        return {"error": "Not enough historical data"}

    print(f"[Backtest] Running {strategy_id} on {symbol} {timeframe} — {len(candles)} candles")

    trades = []
    i = 60  # minimum candles for detection

    while i < len(candles) - 5:
        window = candles[:i]
        result = None

        for detector in [
            lambda c, s: detect_smc(c, s, timeframe),
            lambda c, s: detect_wyckoff(c, s),
            lambda c, s: detect_classic(c, s),
        ]:
            result = detector(window, strategy)
            if result:
                break

        if result and result["entry"] != result["stop"]:
            rr = abs(result["target"] - result["entry"]) / abs(result["entry"] - result["stop"])
            if rr >= strategy.get("min_rr", 2.0):
                trade = simulate_trade(candles, result, i)
                trade.update({
                    "symbol": symbol, "strategy": strategy_id,
                    "timeframe": timeframe, "candle_idx": i,
                    "timestamp": candles[i]["timestamp"],
                })
                trades.append(trade)
                i += 20
                continue

        i += 1

    metrics = calculate_metrics(trades)
    print(f"[Backtest] Done: {metrics.get('total_trades', 0)} trades, "
          f"WR:{metrics.get('win_rate', 0)}% RR:{metrics.get('avg_rr', 0)}")

    return {
        "strategy": strategy_id, "symbol": symbol, "timeframe": timeframe,
        "candles_analyzed": len(candles), "metrics": metrics, "trades": trades,
    }
