# app/api.py

from fastapi import APIRouter, Query
from app.utils import load_phrases

router = APIRouter()
phrases = load_phrases()

@router.get("/api/phrase")
def get_phrase(text: str = Query(...)):
    return phrases.get(text) or {"error": "Phrase not found"}