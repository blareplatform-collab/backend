"""BLARE backtest route."""
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
from engine.backtest import run_backtest
from config.firebase import get_db

router = APIRouter()


class BacktestRequest(BaseModel):
    strategy_id: str
    symbol: str
    timeframe: str = "4h"
    limit: int = 500


@router.post("/")
async def run_backtest_endpoint(req: BacktestRequest):
    result = await run_backtest(req.strategy_id, req.symbol, req.timeframe, req.limit)

    if "metrics" in result:
        try:
            db = get_db()
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
    try:
        db = get_db()
        docs = (db.collection("backtests")
                  .order_by("created_at", direction="DESCENDING")
                  .limit(limit).stream())
        return {"backtests": [doc.to_dict() for doc in docs]}
    except Exception as e:
        return {"error": str(e), "backtests": []}
