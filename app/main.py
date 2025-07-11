from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from linebot.models import AudioSendMessage
import os
from dotenv import load_dotenv


load_dotenv()

import json
import re
import logging

logger = logging.getLogger("uvicorn")

# ✅ Define FastAPI first

app = FastAPI()

# 🧩 Route imports AFTER app is defined

from app.routes import audio #, chat, quiz
from app.routes.ping.ping import router as ping_router
from app.routes.chat.chat import router as chat_router
app.include_router(chat_router)

from app.routes.healthcheck.healthcheck import router as healthcheck_router
app.include_router(healthcheck_router)


def normalize_phrase_key(key: str) -> str:
    return key.strip().replace(" ", "").lower()

# 🔗 Register routes

app.include_router(audio.router)
app.include_router(ping_router)
# app.include_router(chat.router)
# app.include_router(quiz.router)

# app.mount("/static", StaticFiles(directory="static"), name="static")



from fastapi.responses import FileResponse
import os

@app.get("/debug-audio")
def debug_audio():
    audio_path = os.path.join(os.path.dirname(__file__), "..", "data", "debug", "xie-xie.mp3")
    if not os.path.isfile(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(audio_path, media_type="audio/mpeg")



# 🔗 Supabase audio base URL
AUDIO_BASE_URL = os.getenv("SUPABASE_AUDIO_BASE")

# 📁 Load phrases from JSON
import os

json_path = os.path.join(os.path.dirname(__file__), "../data/phrases.json")
with open(json_path, encoding="utf-8") as f:
    raw_phrases = json.load(f)

# 🧠 Normalize Chinese keys
phrases = {
    normalize_phrase_key(k): v
    for k, v in raw_phrases.items()
}

# 🧭 Build reverse map: normalized pinyin → Chinese phrase (unmodified key)
pinyin_aliases = {
    normalize_phrase_key(v["pinyin"]): k  # original Chinese phrase key
    for k, v in raw_phrases.items()
}
logger.info(f"Alias map preview: {pinyin_aliases}")
logger.info(f"🔍 Phrases dict keys: {list(phrases.keys())}")
logger.info(f"🔁 Pinyin alias map: {pinyin_aliases}")

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
def get_phrase(text: str = Query(...)):
    incoming = normalize_phrase_key(text)
    mapped_key = pinyin_aliases.get(incoming, incoming)
    normalized_key = normalize_phrase_key(mapped_key)
    phrase = phrases.get(normalized_key)
   
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    filename = format_audio_filename(phrase["pinyin"])
    audio_url = AUDIO_BASE_URL + filename

    return {
        "input": mapped_key,
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
    incoming = normalize_phrase_key(event.message.text)
    mapped_key = pinyin_aliases.get(incoming, incoming)

    logger.info(f"Incoming: {event.message.text} → Normalized: {incoming} → Mapped key: {mapped_key}")

    phrase = phrases.get(mapped_key)

    from linebot.models import TextSendMessage, AudioSendMessage

    if phrase:
        # build and send messages 
        reply_text = f"{event.message.text} ({phrase['pinyin']}): {phrase['translation']}"
        filename = format_audio_filename(phrase["pinyin"])
        audio_url = AUDIO_BASE_URL + filename

        messages = [
            TextSendMessage(text=reply_text),
            AudioSendMessage(original_content_url=audio_url, duration=3000)
        ]
    else:
        # use LLM fallback and send messages
        from utils.llm_client import chat
        from utils.json_utils import extract_json  # Or wherever you store extract_json()




        # Build LLM prompt
        llm_messages = [
            {
                "role": "system",
                "content": (
                    "You are a native Mandarin tutor. Reply ONLY with a JSON object containing: "
                    "'pinyin', 'translation', 'audio', 'category', 'level', 'quiz', 'culture'. "
                    f"Explain the phrase: {event.message.text}"
                )
            }
        ]

        response = chat(llm_messages)
        cleaned = extract_json(response)

        if not cleaned:
            reply_text = "🤖 I heard you, but couldn't process that phrase just yet."
            messages = [TextSendMessage(text=reply_text)]
        else:
            try:
                entry = json.loads(cleaned)

                # Save to phrases dict
                normalized_key = normalize_phrase_key(event.message.text)
                phrases[normalized_key] = entry

                # Also save back to disk
                json_path = os.path.join(os.path.dirname(__file__), "../data/phrases.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(phrases, f, ensure_ascii=False, indent=2)

                reply_text = (
                    f"{event.message.text} ({entry['pinyin']}) — {entry['translation']}\n\n"
                    f"🎧 {entry['audio']}\n"
                    f"📖 {entry['culture']}\n"
                    f"🧪 {entry['quiz']['question']}\n"
                    f"Options: {', '.join(entry['quiz']['options'])}"
                )
                messages = [TextSendMessage(text=reply_text)]

            except Exception as e:
                messages = [TextSendMessage(text=f"❌ Couldn't parse tutor response: {e}")]

        try:
            line_bot_api.reply_message(event.reply_token, messages)
        except Exception as e:
            logger.error(f"LINE reply error: {e}")

   
print("🧪 SUPABASE_URL =", os.getenv("SUPABASE_URL"))
print("🧪 SUPABASE_KEY =", os.getenv("SUPABASE_KEY")[:6], "...")  # show first few characters
    