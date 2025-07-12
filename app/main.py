from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.utils import (
    add_to_generate_file,
    update_phrase_map
)
import os, json, re, logging, requests

# 🔧 Environment setup
load_dotenv()

logger = logging.getLogger("uvicorn")
AUDIO_BASE_URL = os.getenv("SUPABASE_AUDIO_BASE")
logger.info(f"🔍 Loaded AUDIO_BASE_URL: {AUDIO_BASE_URL}")

# 🚀 FastAPI instance
app = FastAPI()

# Integate Ollama LLM client


OLLAMA_URL = "http://localhost:11434/api/generate"

@app.post("/line-webhook")
async def line_webhook(request: Request):
    data = await request.json()
    user_text = data['events'][0]['message']['text']

    # Send to Ollama
    response = requests.post(OLLAMA_URL, json={"prompt": user_text, "model": "llama3"})
    result = response.json()['response']  # Depends on Ollama model's return structure

    # TODO: Send `result` back to LINE user using the Messaging API
    return {"reply": result}


# Example usage:
add_to_generate_file({
    "title": "New Lesson",
    "prompt": "How do classifiers work in Mandarin?",
    "response": "Classifiers are used in Chinese when counting or specifying nouns..."
})

# 📁 Route imports
from app.routes import audio
from app.routes.ping.ping import router as ping_router
from app.routes.chat.chat import router as chat_router
from app.routes.healthcheck.healthcheck import router as healthcheck_router

app.include_router(audio.router)
app.include_router(ping_router)
app.include_router(chat_router)
app.include_router(healthcheck_router)

# 🎧 Debug audio endpoint
@app.get("/debug-audio")
def debug_audio():
    audio_path = os.path.join(os.path.dirname(__file__), "..", "data", "debug", "xie-xie.mp3")
    if not os.path.isfile(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(audio_path, media_type="audio/mpeg")

# 🌍 Supabase audio base URL
AUDIO_BASE_URL = os.getenv("SUPABASE_AUDIO_BASE")
if not AUDIO_BASE_URL:
    logger.error("❌ SUPABASE_AUDIO_BASE not set — check your .env or Render env")

# 🧠 Phrase utilities
def normalize_phrase_key(key: str) -> str:
    return key.strip().replace(" ", "").lower()

def format_audio_filename(pinyin: str) -> str:
    tone_map = {
        r"[āáǎà]": "a", r"[ēéěè]": "e", r"[īíǐì]": "i",
        r"[ōóǒò]": "o", r"[ūúǔù]": "u", r"[üǖǘǚǜ]": "u"
    }
    for pattern, replacement in tone_map.items():
        pinyin = re.sub(pattern, replacement, pinyin)
    return pinyin.replace(" ", "-").strip().lower() + ".mp3"

def extract_json(text: str) -> str:
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    return match.group(0) if match else None

# 📘 Load phrases
json_path = os.path.join(os.path.dirname(__file__), "../data/phrases.json")
with open(json_path, encoding="utf-8") as f:
    raw_phrases = json.load(f)

phrases = {normalize_phrase_key(k): v for k, v in raw_phrases.items()}
pinyin_aliases = {normalize_phrase_key(v["pinyin"]): k for k, v in raw_phrases.items()}

logger.info(f"Alias map preview: {pinyin_aliases}")
logger.info(f"🔍 Phrases dict keys: {list(phrases.keys())}")

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/api/phrase")
def get_phrase(text: str = Query(...)):
    incoming = normalize_phrase_key(text)
    mapped_key = pinyin_aliases.get(incoming, incoming)
    normalized_key = normalize_phrase_key(mapped_key)
    phrase = phrases.get(normalized_key)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    filename = format_audio_filename(phrase["pinyin"])
    audio_url = (AUDIO_BASE_URL.strip() + filename.strip()).strip()

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

# 🔗 LINE integration
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    AudioSendMessage, StickerMessage
)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.post("/webhook")
async def webhook(req: Request):
    body = await req.body()
    signature = req.headers.get("X-Line-Signature", "")
    logger.info(f"🧪 Raw LINE body: {body}")
    logger.info(f"🧪 Signature: {signature}")
    try:
        handler.handle(body.decode("utf-8"), signature)
    except Exception as e:
        logger.error(f"🔥 Webhook handler error: {e}")
    return "OK"

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    line_bot_api.reply_message(event.reply_token, [
        TextSendMessage(text="👀 Stickers are cool — but I only process Mandarin phrases for now.")
    ])

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    logger.info("✅ LINE TextMessage handler triggered")

    incoming = normalize_phrase_key(event.message.text)
    mapped_key = pinyin_aliases.get(incoming, incoming)
    logger.info(f"Incoming: {event.message.text} → Normalized: {incoming} → Mapped key: {mapped_key}")

    phrase = phrases.get(mapped_key)

    if phrase:
        reply_text = f"{event.message.text} ({phrase['pinyin']}): {phrase['translation']}"
        filename = format_audio_filename(phrase["pinyin"])
        audio_url = (AUDIO_BASE_URL.strip() + filename.strip()).strip()
        messages = [
            TextSendMessage(text=reply_text),
            AudioSendMessage(original_content_url=audio_url, duration=3000)
        ]
    else:
        from utils.llm_client import chat

        llm_messages = [{
            "role": "system",
            "content": (
                "You are a native Mandarin tutor. Reply ONLY with a JSON object containing: "
                "'pinyin', 'translation', 'audio', 'category', 'level', 'quiz', 'culture'. "
                f"Explain the phrase: {event.message.text}"
            )
        }]

        response = chat(llm_messages)
        cleaned = extract_json(response)

if not cleaned:
    # 🔄 Try fallback response from Ollama
    def get_ollama_response(prompt: str) -> str:
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"prompt": prompt, "model": "llama3"}
            )
            return response.json().get("response", "🤖 Ollama didn’t reply.")
        except Exception as e:
            logger.error(f"❌ Ollama error: {e}")
            return f"⚠️ Error reaching Ollama: {e}"

    ollama_text = get_ollama_response(event.message.text)
    messages = [TextSendMessage(text=f"🧠 Tutor says: {ollama_text}")]
else:
    try:
        entry = json.loads(cleaned)
        normalized_key = normalize_phrase_key(event.message.text)
        entry["phrase"] = event.message.text

        # 🧠 Add to memory (runtime dict)
        phrases[normalized_key] = entry

        # 🗂️ Write back to phrase_map.json
        try:
            update_phrase_map(entry)  # This updates the file permanently
            logger.info(f"✅ Updated phrase_map.json with: {entry['phrase']}")
        except Exception as e:
            logger.error(f"❌ Failed to update phrase_map.json: {e}")

        # 📘 Log to generate.json for content tracking
        try:
            add_to_generate_file({
                "title": event.message.text,
                "prompt": event.message.text,
                "response": json.dumps(entry, ensure_ascii=False)
            })
            logger.info(f"✅ Logged tutor output to generate.json")
        except Exception as e:
            logger.error(f"❌ Failed to write to generate.json: {e}")

        # 🔊 Prepare audio response
        filename = format_audio_filename(entry["pinyin"])
        audio_url = (AUDIO_BASE_URL.strip() + filename.strip()).strip()

        reply_text = (
            f"{event.message.text} ({entry['pinyin']}) — {entry['translation']}\n\n"
            f"🎧 {entry['audio']}\n"
            f"📖 {entry['culture']}\n"
            f"🧪 {entry['quiz']['question']}\n"
            f"Options: {', '.join(entry['quiz']['options'])}"
        )

        messages = [
            TextSendMessage(text=reply_text),
            AudioSendMessage(original_content_url=audio_url, duration=3000)
        ]
    except Exception as e:
        messages = [TextSendMessage(text=f"❌ Couldn't parse tutor response: {e}")]
                )

                messages = [
                    TextSendMessage(text=reply_text),
                    AudioSendMessage(original_content_url=audio_url, duration=3000)
                ]
            except Exception as e:
                messages = [TextSendMessage(text=f"❌ Couldn't parse tutor response: {e}")]

    try:
        line_bot_api.reply_message(event.reply_token, messages)
        logger.info(f"✅ Reply sent: {messages}")
    except Exception as e:
        logger.error(f"LINE reply error: {e}")
        logger.info(f"Reply payload: {messages}")
        logger.info(f"Reply token: {event.reply_token}")

# 🧪 Visual env check
print("🧪 SUPABASE_URL =", os.getenv("SUPABASE_URL"))
print("🧪 SUPABASE_KEY =", os.getenv("SUPABASE_KEY")[:6], "...")