import sys
import os
import json
import re

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from utils.llm_client import chat

def build_prompt(phrase):
    return [
        {
            "role": "system",
            "content": (
                "You are a native Mandarin tutor. Return a JSON object with keys: "
                "'pinyin', 'translation', 'audio', 'category', 'level', 'quiz', 'culture'. "
                "Respond ONLY with the JSON object — do not include markdown, commentary, or explanations. "
                f"Explain the phrase: {phrase}"
            )
        }
    ]

def extract_json(text):
    match = re.search(r"```(?:json)?\s*({.*?})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"({.*})", text, re.DOTALL)
    return match.group(1) if match else None

def main():
    # Load phrase map
    try:
        with open("data/phrase_map.json", encoding="utf-8") as f:
            phrase_map = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to load phrase_map.json: {e}")
        phrase_map = {}

    # Load seed list
    try:
        with open("data/seed_list.json", encoding="utf-8") as f:
            seed_list = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to load seed_list.json: {e}")
        seed_list = []

    # Process each seed phrase
    for phrase in seed_list:
        if phrase in phrase_map:
            continue  # Skip existing

        print(f"🧠 Generating for: {phrase}")
        messages = build_prompt(phrase)
        response = chat(messages)

        cleaned = extract_json(response)
        if not cleaned:
            print(f"❌ Could not extract JSON for: {phrase}\nFull response:\n{response}\n")
            continue

        try:
            entry = json.loads(cleaned)

            # ✅ Validate required keys
            required_keys = {"pinyin", "translation", "audio", "category", "level", "quiz", "culture"}
            missing = required_keys - set(entry.keys())
            if missing:
                print(f"⚠️ Incomplete data for '{phrase}': missing keys {missing}")
                continue

            # Auto-fill audio URL if missing
            if not entry.get("audio"):
                slug = phrase.replace(" ", "-")
                entry["audio"] = f"https://your-audio-link.com/{slug}.mp3"

            phrase_map[phrase] = entry
            print(f"✅ Stored: {phrase} → {entry['translation']}")

        except Exception as e:
            print(f"❌ Failed to parse JSON for {phrase}: {e}\nCleaned:\n{cleaned}\n")

    # Save merged phrases
    with open("data/phrases.json", "w", encoding="utf-8") as f:
        json.dump(phrase_map, f, ensure_ascii=False, indent=2)

    print("📦 phrases.json successfully updated.")

if __name__ == "__main__":
    main()