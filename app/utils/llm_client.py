import os
import requests
from dotenv import load_dotenv

load_dotenv()

USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"
OLLAMA_URL = "http://localhost:11434/api/chat"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def chat(messages, model="llama3"):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }

    try:
        if USE_OLLAMA:
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            return response.json()["message"]["content"]
        else:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ LLM error: {str(e)}"