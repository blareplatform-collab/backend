"""BLARE signals route."""
from fastapi import APIRouter, Query, HTTPException
from config.firebase import get_db
from execution.router import execute_signal

router = APIRouter()


@router.get("/")
async def get_signals(limit: int = Query(default=20, le=100)):
    try:
        db = get_db()
        docs = (db.collection("signals")
                  .order_by("created_at", direction="DESCENDING")
                  .limit(limit)
                  .stream())
        signals = [doc.to_dict() for doc in docs]
        return {"count": len(signals), "signals": signals}
    except Exception as e:
        return {"error": str(e), "signals": []}


@router.get("/{signal_id}")
async def get_signal(signal_id: str):
    try:
        db = get_db()
        doc = db.collection("signals").document(signal_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Signal not found")
        return doc.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{signal_id}/reject")
async def reject_signal(signal_id: str):
    try:
        db = get_db()
        db.collection("signals").document(signal_id).update({"status": "rejected"})
        return {"status": "rejected", "signal_id": signal_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
