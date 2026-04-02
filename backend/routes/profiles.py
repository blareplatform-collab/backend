"""BLARE profiles routes."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def get_profiles():
    return {"profiles": [], "message": "Profiles endpoint ready"}
