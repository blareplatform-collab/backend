"""BLARE strategies route."""
from fastapi import APIRouter, HTTPException
from engine.loader import get_strategies, get_strategy

router = APIRouter()


@router.get("/")
async def list_strategies():
    strategies = get_strategies()
    return {
        "count": len(strategies),
        "strategies": [
            {
                "id": s["id"],
                "name": s["name"],
                "market": s["market"],
                "direction": s["direction"],
                "timeframes": {"htf": s["htf"], "mtf": s["mtf"], "ltf": s["ltf"]},
                "min_rr": s["min_rr"],
                "conditions_count": len(s["conditions"]),
            }
            for s in strategies.values()
        ]
    }


@router.get("/{strategy_id}")
async def get_strategy_detail(strategy_id: str):
    strategy = get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy
