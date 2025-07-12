import json, os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 🔒 Resolve path safely
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
os.makedirs(DATA_DIR, exist_ok=True)  # Make sure data dir exists
MISSING_LOG_PATH = os.path.join(DATA_DIR, "missing.json")

def log_missing_phrase(phrase: str, source: str = "static_lookup", user_id: str = None):
    print(f"✅ log_missing_phrase() triggered for: {phrase}")

    entry = {
        "phrase": phrase,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if user_id:
        entry["user_id"] = user_id

    print(f"🧭 Logging to path: {MISSING_LOG_PATH}")
    print(f"📂 Current working directory: {os.getcwd()}")
    logger.info(f"📁 Logging phrase to: {MISSING_LOG_PATH}")

    try:
        if os.path.exists(MISSING_LOG_PATH):
            with open(MISSING_LOG_PATH, encoding="utf-8") as f:
                existing = json.load(f)
                print(f"📦 Existing log entries loaded: {len(existing)}")
                if not isinstance(existing, list):
                    print(f"⚠️ Invalid format, expected list — got {type(existing)}")
                    logger.warning(f"⚠️ Invalid format in {MISSING_LOG_PATH}, resetting to list.")
                    existing = []
        else:
            print("📂 missing.json does not exist, starting fresh")
            existing = []
    except Exception as e:
        logger.error(f"❌ Error loading {MISSING_LOG_PATH}: {e}")
        print(f"❌ Error loading {MISSING_LOG_PATH}: {e}")
        existing = []

    if any(p.get("phrase") == phrase and p.get("user_id") == user_id for p in existing):
        print(f"⏭ Skipping duplicate: '{phrase}'")
        logger.info(f"⏭ Phrase already logged, skipping: '{phrase}'")
        return

    existing.append(entry)
    print(f"➕ Added new entry: {entry}")

    try:
        with open(MISSING_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
            print(f"✅ Write successful. Total entries: {len(existing)}")
        logger.info(f"📝 Logged missing phrase: '{phrase}' from '{source}' by user '{user_id}'")
    except Exception as e:
        logger.error(f"❌ Failed to write to {MISSING_LOG_PATH}: {e}")
        print(f"❌ Failed to write to {MISSING_LOG_PATH}: {e}")
        print(f"📂 Current working directory: {os.getcwd()}")