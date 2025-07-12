from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import json

router = APIRouter()

@router.get("/debug/missing")
def get_missing_phrases():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/missing.json"))
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)