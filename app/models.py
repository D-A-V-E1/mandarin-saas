from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import json

app = FastAPI()

# Load phrases from JSON file
def load_phrases():
    with open("data/phrases.json", "r", encoding="utf-8") as f:
        return json.load(f)

phrases = load_phrases()