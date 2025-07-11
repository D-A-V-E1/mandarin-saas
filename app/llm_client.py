
import os
import requests

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
if USE_OLLAMA:
        response = requests.post(OLLAMA_URL, json=payload)
    else:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
return response.json()["message"]["content"] if USE_OLLAMA else response.json()["choices"][0]["message"]["content"]
