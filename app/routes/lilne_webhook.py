import json
from fastapi import APIRouter, Request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from utils.llm_client import chat
from utils.json_utils import extract_json  # You'll create this helper or import from your script

LINE_CHANNEL_ACCESS_TOKEN = "your_token"
LINE_CHANNEL_SECRET = "your_secret"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

router = APIRouter()

# Load phrase map at startup
with open("data/phrases.json", encoding="utf-8") as f:
    phrase_map = json.load(f)

@router.post("/line_webhook")
async def line_webhook(request: Request):
    body = await request.body()
    signature = request.headers["X-Line-Signature"]

    try:
        handler.handle(body.decode("utf-8"), signature)
    except Exception as e:
        print(f"⚠️ LINE webhook error: {e}")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()

    if text in phrase_map:
        data = phrase_map[text]
        reply_text = (
            f"{text} ({data['pinyin']}) — {data['translation']}\n\n"
            f"🎧 {data['audio']}\n📖 {data['culture']}\n"
            f"🧪 {data['quiz']['question']}\n"
            f"Options: {', '.join(data['quiz']['options'])}"
        )
    else:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a native Mandarin tutor. Respond in pure JSON with keys: "
                    "'pinyin', 'translation', 'audio', 'category', 'level', 'quiz', 'culture'. "
                    f"Explain the phrase: {text}"
                )
            }
        ]
        response = chat(messages)
        cleaned = extract_json(response)
        if not cleaned:
            reply_text = "🤖 Sorry, I couldn't understand that phrase."
        else:
            try:
                entry = json.loads(cleaned)
                phrase_map[text] = entry
                with open("data/phrases.json", "w", encoding="utf-8") as f:
                    json.dump(phrase_map, f, ensure_ascii=False, indent=2)

                reply_text = (
                    f"{text} ({entry['pinyin']}) — {entry['translation']}\n\n"
                    f"🎧 {entry['audio']}\n📖 {entry['culture']}\n"
                    f"🧪 {entry['quiz']['question']}\n"
                    f"Options: {', '.join(entry['quiz']['options'])}"
                )
            except Exception as e:
                reply_text = f"❌ Failed to parse response: {e}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
