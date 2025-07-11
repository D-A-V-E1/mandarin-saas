
from dotenv import load_dotenv
load_dotenv()
from fastapi import APIRouter
import os
import uuid
import asyncio
import edge_tts
from supabase import create_client

router = APIRouter()

# Load Supabase credentials from .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AUDIO_BUCKET = os.getenv("AUDIO_BUCKET_NAME")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# TTS + Upload function
async def generate_and_upload_tts(text: str) -> str:
    filename = f"{uuid.uuid4()}.mp3"
    local_path = f"temp/{filename}"

    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save(local_path)

    # Upload to Supabase
    with open(local_path, "rb") as f:
        supabase.storage.from_(AUDIO_BUCKET).upload(filename, f)

    # Return public audio URL
    return f"{SUPABASE_URL}/storage/v1/object/public/{AUDIO_BUCKET}/{filename}"

# FastAPI endpoint
@router.get("/api/audio")
async def get_audio(text: str):
    audio_url = await generate_and_upload_tts(text)
    return {"audio_url": audio_url}