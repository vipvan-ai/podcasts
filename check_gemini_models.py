import os
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAqMBniCg-vSQPxvTeYibsvIzGmAxewPuc")

client = genai.Client(api_key=GEMINI_API_KEY)

print("Listing available models from Google GenAI SDK...")
try:
    models = list(client.models.list())
    for m in models:
        name = getattr(m, 'name', str(m))
        if 'tts' in name.lower() or 'audio' in name.lower() or 'speech' in name.lower() or '3.' in name.lower() or 'flash' in name.lower():
            print(f"- {name}")
except Exception as e:
    print(f"Error listing models: {e}")
