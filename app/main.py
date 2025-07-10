from fastapi import FastAPI, Query, HTTPException
import json
import re

app = FastAPI()

# 🔗 Supabase audio base URL
AUDIO_BASE_URL = "https://bingolingo.supabase.co/storage/v1/object/public/mandarinaudio/"

# 📁 Load phrases from JSON
with open("phrases.json", encoding="utf-8") as f:
    phrases = json.load(f)

# 🧹 Clean pinyin for filenames
def format_audio_filename(pinyin: str) -> str:
    tone_map = {
        r"[āáǎà]": "a", r"[ēéěè]": "e", r"[īíǐì]": "i",
        r"[ōóǒò]": "o", r"[ūúǔù]": "u", r"[üǖǘǚǜ]": "u"
    }
    for pattern, replacement in tone_map.items():
        pinyin = re.sub(pattern, replacement, pinyin)
    return pinyin.replace(" ", "-").lower() + ".mp3"

# 🌱 Root route for sanity check
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

# 🔎 Phrase endpoint (dynamic response)
@app.get("/api/phrase")
def get_phrase(text: str = Query(..., description="The phrase to translate")):
    phrase = phrases.get(text)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    filename = format_audio_filename(phrase["pinyin"])
    audio_url = AUDIO_BASE_URL + filename

    return {
        "input": text,
        "translation": phrase["translation"],
        "pinyin": phrase["pinyin"],
        "audio_url": audio_url,
        "category": phrase.get("category"),
        "level": phrase.get("level"),
        "quiz": phrase.get("quiz"),
        "cultural_note": phrase.get("culture")
    }

from fastapi import Request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.post("/webhook")
async def webhook(req: Request):
    body = await req.body()
    signature = req.headers.get("X-Line-Signature", "")

    try:
        handler.handle(body.decode("utf-8"), signature)
    except Exception as e:
        return {"error": str(e)}

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    phrase = phrases.get(text)

    if phrase:
        reply = f"{text} ({phrase['pinyin']}): {phrase['translation']}"
    else:
        reply = "Sorry, I don't recognize that phrase yet 😅"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )