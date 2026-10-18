import os
import io
import time
import base64
import requests
import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

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

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()

if not SARVAM_API_KEY:
    raise ValueError("SARVAM_API_KEY is not set in .env")

# Conversational Hinglish Multi-Speaker Podcast Dialogue
# Hosts: Shubh (shubh_enhi_companion) & Ishita (ishita_enhi_companion)
# Topic: Vibe Coding, AI FOMO, and Engineering Reality
DIALOGUE_TURNS = [
    {
        "speaker": "Shubh",
        "voice": "shubh_enhi_companion",
        "lang": "hi-IN",
        "text": "Yaar Ishita, honestly ek baat batao... kya tumhe bhi lagta hai ki aaj kal tech world me kuch zyada hi FOMO chal raha hai? Like, coffee shop jao ya Twitter kholo, har koi bas agentic workflows aur prompt engineering ki baatein kar raha hai!"
    },
    {
        "speaker": "Ishita",
        "voice": "ishita_enhi_companion",
        "lang": "hi-IN",
        "text": "Haha, totally Shubh! Kal hi ek founder friend bol raha tha—'Yaar maine weekend pe vibe coding karke pura SaaS product khada kar diya, bas ab direct seed funding uthayenge!' Main toh sunke hi dang reh gayi."
    },
    {
        "speaker": "Shubh",
        "voice": "shubh_enhi_companion",
        "lang": "hi-IN",
        "text": "Exactly yaar! Vibe coding sunne me kitna cool sound karta hai, lekin jab production me edge cases aate hain aur database crash hota hai, tab saari vibes gayab ho jaati hain aur real engineering shuru hoti hai—woh bhi raat ke do baje cold coffee ke saath!"
    },
    {
        "speaker": "Ishita",
        "voice": "ishita_enhi_companion",
        "lang": "hi-IN",
        "text": "Sach me! AI tools humara time zaroor bacha sakte hain, lekin real creativity aur problem solving abhi bhi humans ke paas hi hai. Toh smart banne ka funda simple hai—AI ko co-pilot banao, autopilot nahi!"
    }
]

def synthesize_turn(text: str, speaker: str, lang: str = "hi-IN") -> bytes:
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": [text],
        "target_language_code": lang,
        "speaker": speaker,
        "pitch": 0,
        "pace": 1.0,
        "loudness": 1.0,
        "speech_sample_rate": 24000,
        "enable_preprocessing": True,
        "model": "bulbul:v4-flash"
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Sarvam API error ({resp.status_code}): {resp.text}")
    
    data = resp.json()
    b64_audio = data["audios"][0]
    return base64.b64decode(b64_audio)

def build_hinglish_sample():
    print("==========================================================")
    print("Synthesizing Hinglish Multi-Speaker Sample with Bulbul 4 (bulbul:v4-flash)")
    print("Speakers: Shubh (shubh_enhi_companion) & Ishita (ishita_enhi_companion)")
    print("Theme: Vibe Coding & AI FOMO")
    print("==========================================================")
    
    combined_samples = []
    target_sr = 24000
    pause_samples = int(target_sr * 0.45) # 450ms natural conversational pause

    b_hp, a_hp = signal.butter(2, 80 / (target_sr / 2), btype='high')

    for idx, turn in enumerate(DIALOGUE_TURNS):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        lang = turn.get("lang", "hi-IN")
        
        print(f"\n[Turn {idx+1}/{len(DIALOGUE_TURNS)}] Synthesizing {speaker} ({voice})...")
        wav_bytes = synthesize_turn(text, voice, lang)
        
        raw_samples, sr = sf.read(io.BytesIO(wav_bytes))
        if sr != target_sr:
            num_samples = int(len(raw_samples) * target_sr / sr)
            raw_samples = signal.resample(raw_samples, num_samples)
            sr = target_sr

        # DC offset removal
        samples = raw_samples.astype(np.float32)
        samples -= np.mean(samples)

        # 80Hz High-pass filter for mic pop removal
        samples = signal.filtfilt(b_hp, a_hp, samples)

        # 20ms Cosine envelope at edges
        fade_len = int(sr * 0.02)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        combined_samples.append(samples)
        if idx < len(DIALOGUE_TURNS) - 1:
            combined_samples.append(np.zeros(pause_samples, dtype=np.float32))

        duration_turn = len(samples) / sr
        print(f" -> Turn {idx+1} synthesized ({duration_turn:.2f}s)")
        time.sleep(0.5)

    full_mix = np.concatenate(combined_samples)

    # Master broadcast peak normalization (-1.0 dBFS)
    max_peak = np.max(np.abs(full_mix))
    if max_peak > 0:
        full_mix = full_mix * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_sarvam_bulbul4_hinglish_conversation_50s.mp3"
    sf.write(str(out_file), full_mix, target_sr)

    total_duration = len(full_mix) / target_sr
    print("\n==========================================================")
    print(f"[SUCCESS] Bulbul 4 Hinglish Multi-Speaker Master Created!")
    print(f"Output File: {out_file}")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print("==========================================================")
    return out_file, total_duration

if __name__ == "__main__":
    build_hinglish_sample()
