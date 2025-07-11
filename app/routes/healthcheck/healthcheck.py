from fastapi import APIRouter
import os
from supabase import create_client, SupabaseException
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

@router.get("/healthcheck")
async def healthcheck():
    # Environment Variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    bucket_name = os.getenv("AUDIO_BUCKET_NAME")

    env_status = {
        "SUPABASE_URL": bool(supabase_url),
        "SUPABASE_KEY": bool(supabase_key),
        "AUDIO_BUCKET_NAME": bool(bucket_name)
    }

    # Supabase Connection Test
    try:
        supabase = create_client(supabase_url, supabase_key)
        bucket_list = supabase.storage.list_buckets()
        supabase_status = "✅ Connected"
    except SupabaseException as e:
        supabase_status = f"❌ Failed: {str(e)}"
    except Exception as e:
        supabase_status = f"❌ Unexpected Error: {str(e)}"

    return {
        "env_vars": env_status,
        "supabase_status": supabase_status,
        "message": "Healthcheck complete 🚀"
    }

print("🚨 /healthcheck route hit")