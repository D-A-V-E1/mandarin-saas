from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
async def ping():
    print("🟢 Ping route is active")
    return {"message": "pong"}