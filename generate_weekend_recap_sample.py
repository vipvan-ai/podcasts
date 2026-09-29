import os
import time
import base64
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

WEEKEND_SCRIPT = [
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "Happy weekend, everyone! Welcome to the Future Human Daily Weekend Recap. Alex and Elena are off taking a well-deserved break today and will be back bright and early Monday morning—so I am Veda with Rami, and we are kicking back with your Saturday morning coffee."
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "[chuckles] That is right! No heavy quantum physics equations today, folks. Just pure weekend vibes and the funniest, wildest tech stories that broke this week."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[playfully] Speaking of wild, Rami... did you catch that video of the new humanoid robot trying to fold laundry?"
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "Oh, I replayed it three times! It took five minutes to fold one t-shirt, and then accidentally threw the matching sock across the living room! [chuckles] Honestly, that is still better than my college roommate used to do."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[laughs] Exactly! The robot looked so proud of itself too. But hey, story number two... an AI model just composed an entire nineteen-eighties synth-wave album that is actually trending on music charts."
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "[thoughtfully] Right? I listened to track three on my morning jog. You literally cannot tell if it was made by a computer or a guy wearing neon leg warmers in nineteen-eighty-four."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[playfully] Well, grab another cup of coffee, folks, because we have a couple more weekend gems to unpack before Alex and Elena get back on Monday!"
    }
]

def clean_turn(samples, sample_rate=24000):
    b, a = signal.butter(2, 80 / (sample_rate / 2), btype='high')
    samples = signal.filtfilt(b, a, samples)

    # 30ms smooth Cosine envelope fade
    fade_len = int(sample_rate * 0.03)
    if len(samples) > 2 * fade_len:
        fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
        fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
        samples[:fade_len] *= fade_in
        samples[-fade_len:] *= fade_out

    return samples

def generate_weekend_sample():
    print("==========================================================", flush=True)
    print("Synthesizing Weekend Recap Sample (Veda & Rami)", flush=True)
    print("==========================================================", flush=True)

    sample_rate = 24000
    combined = []
    silence_gap = np.zeros(int(sample_rate * 0.38), dtype=np.float32)

    TTS_MODELS = [
        'gemini-3.8-flash-lite-tts',
        'gemini-3.8-flash-tts'
    ]

    for idx, turn in enumerate(WEEKEND_SCRIPT):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]

        raw_bytes = None
        for model in TTS_MODELS:
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                            )
                        )
                    )
                )
                part = resp.candidates[0].content.parts[0]
                if part.inline_data:
                    data = part.inline_data.data
                    if isinstance(data, str): data = base64.b64decode(data)
                    raw_bytes = data
                    print(f" -> Turn {idx+1}/{len(WEEKEND_SCRIPT)} [{speaker} ({voice})] via {model}", flush=True)
                    break
            except Exception as e:
                time.sleep(2)

        if raw_bytes:
            s = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            cleaned = clean_turn(s, sample_rate)
            combined.append(cleaned)
            combined.append(silence_gap)
            time.sleep(2)

    full = np.concatenate(combined)
    max_p = np.max(np.abs(full))
    if max_p > 0: full = full * (0.891 / max_p)

    out_path = AUDIO_DIR / "sample_16_weekend_recap_veda_rami.mp3"
    sf.write(str(out_path), full, sample_rate)
    duration = len(full) / sample_rate
    print("==========================================================", flush=True)
    print(f"[COMPLETE] Saved Weekend Recap Sample: {out_path}", flush=True)
    print(f"Duration: {duration:.2f}s", flush=True)
    print("==========================================================", flush=True)

if __name__ == "__main__":
    generate_weekend_sample()
