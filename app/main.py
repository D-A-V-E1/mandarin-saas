
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/api/phrase")
def get_phrase(text: str = Query(..., description="The phrase to translate")):
    # Dummy response for now
    return {
        "input": text,
        "translation": "Hello",
        "pinyin": "nǐ hǎo",
        "audio_url": "https://example.com/audio/nihao.mp3",
        "cultural_note": "Used as a common greeting in Mandarin."
    }