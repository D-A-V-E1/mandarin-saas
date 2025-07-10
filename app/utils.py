# app/utils.py

import json

def load_phrases(path="data/phrases.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
    def generate_audio_url(phrase_key):
    base_url = "https://your-supabase-url.supabase.co/storage/v1/object/public/mandarinaudio/"
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
        # Add more mappings
    }
    return base_url + file_map.get(phrase_key, "default.mp3")

