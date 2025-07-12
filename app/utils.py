# app/utils.py

import json
import os

def load_phrases(path="data/phrases.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_audio_url(phrase_key):
    base_url = "https://bawoozkowhxcybbplw.supabase.co/storage/v1/object/public/mandarinaudio/"
    file_map = {
        "你好": "ni-hao.mp3",
        "谢谢": "xie-xie.mp3",
        "再见": "zai-jian.mp3",
        "请问": "qing-wen.mp3",
        "对不起": "dui-bu-qi.mp3",
        "没关系": "mei-guan-xi.mp3",
        "我不懂": "wo-bu-dong.mp3",
        "我会说一点中文": "hui-shuo-yi-dian.mp3",
        "厕所在哪里": "ce-suo.mp3",
        "多少钱": "duo-shao-qian.mp3",
        # Add more mappings as needed
    }
    return base_url + file_map.get(phrase_key, "default.mp3")

def add_to_generate_file(new_item: dict, file_path: str = "generate.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    data.append(new_item)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_phrase_map(new_item: dict, file_path: str = os.path.join("mandarin-saas", "data", "phrase_map.json")):
    """
    Adds or updates a phrase entry in the phrase_map.json file.
    Automatically fills in the audio_url using generate_audio_url() if not provided.
    Example new_item:
        {
            "phrase": "谢谢",
            "pinyin": "xie-xie",
            "meaning": "thank you",
            "examples": ["谢谢你", "不客气"]
        }
    """
    if "phrase" not in new_item:
        raise ValueError("Missing required key: 'phrase'")

    # Auto-populate audio URL if missing
    if "audio_url" not in new_item:
        new_item["audio_url"] = generate_audio_url(new_item["phrase"])

    # Load existing data
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # Update or insert the item
    phrase_key = new_item["phrase"]
    data[phrase_key] = new_item

    # Write back to file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Phrase '{phrase_key}' added or updated in phrase_map.json")