"""BLARE trades route."""
from fastapi import APIRouter, Query
from config.firebase import get_db

router = APIRouter()


@router.get("/")
async def get_trades(limit: int = Query(default=20, le=100)):
    try:
        db = get_db()
        docs = (db.collection("trades")
                  .order_by("opened_at", direction="DESCENDING")
                  .limit(limit)
                  .stream())
        return {"trades": [doc.to_dict() for doc in docs]}
    except Exception as e:
        return {"error": str(e), "trades": []}


@router.get("/open")
async def get_open_positions():
    try:
        db = get_db()
        docs = db.collection("trades").where("status", "==", "open").stream()
        return {"positions": [doc.to_dict() for doc in docs]}
    except Exception as e:
        return {"error": str(e), "positions": []}
