from fastapi import APIRouter, Request
from ...utils.llm_client import chat

router = APIRouter()

@router.post("/api/chat")
async def handle_chat(request: Request):
    body = await request.json()
    user_text = body.get("text")

    if not user_text:
        return {"error": "Missing user input"}

    messages = [
        {"role": "system", "content": "You are a helpful Mandarin tutor."},
        {"role": "user", "content": user_text}
    ]

    reply = chat(messages)
    return {"reply": reply}