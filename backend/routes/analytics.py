"""BLARE analytics route."""
from fastapi import APIRouter
from config.firebase import get_db

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary():
    try:
        db = get_db()
        trades = [doc.to_dict() for doc in db.collection("trades").stream()]
        signals = [doc.to_dict() for doc in
                   db.collection("signals")
                     .where("status", "in", ["executed", "rejected"]).stream()]

        if not trades:
            return {"message": "No trades yet", "total_trades": 0,
                    "win_rate": 0, "total_pnl": 0, "strategy_stats": {},
                    "high_conf_signals": 0, "low_conf_signals": 0}

        closed = [t for t in trades if t.get("pnl") is not None]
        wins = [t for t in closed if t.get("pnl", 0) > 0]

        strategy_stats = {}
        for t in closed:
            sid = t.get("strategy", "unknown")
            if sid not in strategy_stats:
                strategy_stats[sid] = {"wins": 0, "losses": 0}
            if t.get("pnl", 0) > 0:
                strategy_stats[sid]["wins"] += 1
            else:
                strategy_stats[sid]["losses"] += 1

        high_conf = [s for s in signals if s.get("confidence", 0) >= 70 and s.get("status") == "executed"]
        low_conf = [s for s in signals if s.get("confidence", 0) < 70 and s.get("status") == "executed"]

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
