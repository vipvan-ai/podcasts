import os
import re
import time
import base64
import numpy as np
import soundfile as sf
from pathlib import Path
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Load .env
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

TTS_MODELS = [
    'gemini-3.8-flash-tts',
    'gemini-3.8-flash-lite-tts',
    'gemini-3.1-flash-tts-preview'
]

# 45-second engaging Hindi dialogue: "Will AI Glasses replace Smartphones?"
# Co-hosts: Rami & Veda
HINDI_DIALOGUE = [
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "नमस्ते दोस्तों! ज़रा सोचिए, अगर आपकी जेब में रखा स्मार्टफ़ोन हमेशा के लिए ग़ायब हो जाए और उसकी जगह सिर्फ़ एक हल्का सा चश्मा आ जाए? आज हम बात कर रहे हैं AI स्मार्ट ग्लासेस की।"
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "बिल्कुल रामी! और सबसे दिलचस्प बात यह है कि आपको स्क्रीन पर उंगलियाँ चलाने की ज़रूरत ही नहीं है। आप किसी इमारत या पौधे को देखते हैं, और AI तुरंत उसका पूरा ब्योरा आपकी आँखों के सामने रख देता है!"
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "लेकिन वेदा, असली पहेली तो यह है—क्या लोग दिनभर चेहरे पर कैमरा और माइक पहनकर घूमने के लिए सच में तैयार हैं? प्राइवेसी का क्या होगा?"
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "यही तो सबसे बड़ा सवाल है, रामी! सुविधा जितनी जादुई लगती है, हमारी निजी ज़िंदगी पर उसकी क़ीमत भी उतनी ही बड़ी हो सकती है। तो चलिए, इस दिलचस्प चर्चा को आगे बढ़ाते हैं!"
    }
]

def synthesize_turn(voice_name, text):
    clean_text = re.sub(r'\[.*?\]', '', text).strip()
    for model_name in TTS_MODELS:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=clean_text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                        )
                    )
                )
            )
            part = resp.candidates[0].content.parts[0]
            if part.inline_data:
                data = part.inline_data.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                print(f" -> Synthesized [{voice_name}] via {model_name}: {clean_text[:40]}...")
                return data
        except Exception as e:
            print(f" -> Model {model_name} rate limit / error: {e}. Retrying next...")
            time.sleep(2)
    return None

def build_hindi_sample():
    print("==========================================================")
    print("Synthesizing 45s Hindi Podcast Sample (Rami & Veda)")
    print("==========================================================")
    
    combined_samples = []
    sample_rate = 24000
    pause_samples = int(sample_rate * 0.38) # 380ms natural conversational pause

    for idx, turn in enumerate(HINDI_DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        
        print(f"\nProcessing Turn {idx+1}/{len(HINDI_DIALOGUE)}: {speaker} ({voice})")
        raw_pcm = synthesize_turn(voice, text)
        if not raw_pcm:
            print(f"Failed turn {idx+1}")
            continue

        samples = np.frombuffer(raw_pcm, dtype=np.int16).astype(np.float32) / 32768.0

        # DC offset removal
        samples -= np.mean(samples)

        # 20ms Cosine Fade-in / Fade-out to eliminate edge clicks
        fade_len = int(sample_rate * 0.02)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        combined_samples.append(samples)
        if idx < len(HINDI_DIALOGUE) - 1:
            combined_samples.append(np.zeros(pause_samples, dtype=np.float32))
            
        time.sleep(1.5)

    if not combined_samples:
        print("[ERROR] No audio generated.")
        return

    full_audio = np.concatenate(combined_samples)
    
    # Broadcast peak normalization to -1.0 dBFS
    max_peak = np.max(np.abs(full_audio))
    if max_peak > 0:
        full_audio = full_audio * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_hindi_podcast_45s.mp3"
    sf.write(str(out_file), full_audio, sample_rate)
    
    duration = len(full_audio) / sample_rate
    print("\n==========================================================")
    print(f"[COMPLETE] Hindi Podcast Sample Saved!")
    print(f"Output File: {out_file}")
    print(f"Duration: {duration:.2f} seconds")
    print("==========================================================")

if __name__ == "__main__":
    build_hindi_sample()
