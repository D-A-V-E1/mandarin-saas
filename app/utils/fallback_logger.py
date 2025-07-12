import json, os
from datetime import datetime

MISSING_LOG_PATH = os.path.join(os.path.dirname(__file__), "../../data/missing.json")

def log_missing_phrase(phrase: str, source: str = "static_lookup", user_id: str = None):
    entry = {
        "phrase": phrase,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if user_id:
        entry["user_id"] = user_id

    # Load existing
    if os.path.exists(MISSING_LOG_PATH):
        with open(MISSING_LOG_PATH, encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except Exception:
                existing = []
    else:
        existing = []

    existing.append(entry)

    with open(MISSING_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)