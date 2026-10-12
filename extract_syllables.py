import os
import json
import re
from dotenv import load_dotenv
load_dotenv('c:/Users/12482/code/podcasts/.env')
from google import genai

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
audio_file = client.files.upload(file='C:/Users/12482/Downloads/tension.mp3')

prompt = """Analyze the speech in this 20.7-second audio file with extreme millisecond accuracy.
Break down every single word and syllable spoken from 0 ms to the end of the audio.
Return ONLY a valid JSON array of objects with the exact schema:
[
  {
    "index": 1,
    "word": "Life",
    "syllable": "Life",
    "phonetic": "laɪf",
    "start_ms": 120,
    "end_ms": 420
  }
]
Do not output markdown codeblocks, just the pure JSON string.
"""

resp = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=[audio_file, prompt]
)

text = resp.text.strip()
if text.startswith("```"):
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

with open('C:/Users/12482/Downloads/syllables_detailed.json', 'w', encoding='utf-8') as f:
    f.write(text.strip())

try:
    data = json.loads(text.strip())
    print(f"Extracted {len(data)} syllables!")
    print("Sample:", data[:3])
except Exception as e:
    print("JSON Parse error:", e)
    print("First 300 chars:", text[:300])
