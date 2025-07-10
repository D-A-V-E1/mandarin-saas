import json
from pprint import pprint

def load_phrases(path="data/phrases.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

phrases = load_phrases()

def inspect_phrase(key):
    if key not in phrases:
        print(f"❌ Phrase '{key}' not found.")
        return

    print(f"🔍 Inspecting phrase: {key}")
    data = phrases[key]
    print(f"- Pinyin: {data.get('pinyin')}")
    print(f"- Translation: {data.get('translation')}")
    print(f"- Audio URL: {data.get('audio')}")
    print(f"- Level: {data.get('level')}")
    print(f"- Category: {data.get('category')}")
    print(f"- Culture Note: {data.get('culture')}")
    
    if "quiz" in data:
        print("📝 Quiz:")
        pprint(data["quiz"])
    else:
        print("⚠️ No quiz attached.")

# 👇 Change this to test any phrase:
inspect_phrase("你好")