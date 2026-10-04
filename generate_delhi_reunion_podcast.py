import os
import sys
import io
import time
import base64
import requests
import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

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

# Energetic & Argumentative Delhiite Hinglish Dialogue
# Topic: School Reunion (स्कूल रीयूनियन)
# Characters: Vipin (Cynical, annoyed Delhiite) vs Ishita (Hyper, persistent Delhiite)
REUNION_DIALOGUE = [
    {
        "speaker": "Ishita",
        "voice": "ishita",
        "pace": 1.14,
        "text": "अरे विपिन! तू पागल हो गया है क्या यार? पूरे दस साल बाद स्कूल रीयूनियन हो रहा है, सारे पुराने बैचमेट्स आ रहे हैं, और तू कह रहा है तू नहीं जाएगा?!"
    },
    {
        "speaker": "Vipin",
        "voice": "rohan",
        "pace": 1.15,
        "text": "हाँ भाई, बिल्कुल नहीं जाऊंगा! क्या रखा है उस रीयूनियन में इशिता? वही फालतू का दिखावा! सब अपना पैकेज, नया स्टार्टअप, और गाड़ी फ्लेक्स करने आ रहे हैं। कौन असली दोस्तों से मिलने आ रहा है भाई?"
    },
    {
        "speaker": "Ishita",
        "voice": "ishita",
        "pace": 1.14,
        "text": "अरे तो तू इतना इनसिक्योर क्यों हो रहा है भाई? सब शो-ऑफ करने थोड़ी आ रहे हैं! कुछ लोग पुरानी यादें, वही कैंटीन के समोसे और स्कूल के किस्से याद करने भी तो आते हैं। तू इतना बोरिंग कब से हो गया यार?!"
    },
    {
        "speaker": "Vipin",
        "voice": "rohan",
        "pace": 1.15,
        "text": "बोरिंग नहीं, प्रैक्टिकल हूँ मैं! पाँच मिनट पुरानी बातें होंगी, और फिर वही शुरू—'अरे तूने गुड़गांव में फ्लैट लिया कि नहीं?' भाई मुझसे ये फेक स्माइल वाला ड्रामा बर्दाश्त नहीं होता, तू जा मजे कर!"
    },
    {
        "speaker": "Ishita",
        "voice": "ishita",
        "pace": 1.16,
        "text": "ओहो विपिन! ड्रामा तू कर रहा है! चुपचाप तैयार हो जा, शाम को सात बजे गाड़ी मैं ड्राइव कर रही हूँ, तुझे चलना ही पड़ेगा!"
    }
]

def synthesize_turn(text: str, speaker: str, pace: float = 1.12) -> bytes:
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": [text],
        "target_language_code": "hi-IN",
        "speaker": speaker,
        "pitch": 0,
        "pace": pace,
        "loudness": 1.1,
        "speech_sample_rate": 24000,
        "enable_preprocessing": True,
        "model": "bulbul:v3"
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Sarvam API error ({resp.status_code}): {resp.text}")
    
    data = resp.json()
    b64_audio = data["audios"][0]
    return base64.b64decode(b64_audio)

def build_reunion_podcast():
    print("==========================================================")
    print("Generating Energetic Delhi Reunion Podcast: Vipin & Ishita")
    print("Vibe: Argumentative Delhiite Hinglish Banter")
    print("==========================================================")

    combined_samples = []
    target_sr = 24000
    # Snappy 200ms argumentative pause between turns (fast comeback rhythm)
    pause_samples = int(target_sr * 0.20)

    b_hp, a_hp = signal.butter(2, 80 / (target_sr / 2), btype='high')

    for idx, turn in enumerate(REUNION_DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        pace = turn["pace"]
        text = turn["text"]
        
        print(f"\n[Turn {idx+1}/{len(REUNION_DIALOGUE)}] {speaker} ({voice}, pace={pace}): {text[:45]}...")
        wav_bytes = synthesize_turn(text, voice, pace)
        
        raw_samples, sr = sf.read(io.BytesIO(wav_bytes))
        if sr != target_sr:
            num_samples = int(len(raw_samples) * target_sr / sr)
            raw_samples = signal.resample(raw_samples, num_samples)
            sr = target_sr

        samples = raw_samples.astype(np.float32)
        samples -= np.mean(samples)
        samples = signal.filtfilt(b_hp, a_hp, samples)

        # 15ms Smooth Cosine Envelope at turn edges
        fade_len = int(sr * 0.015)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        combined_samples.append(samples)
        if idx < len(REUNION_DIALOGUE) - 1:
            combined_samples.append(np.zeros(pause_samples, dtype=np.float32))

        t_dur = len(samples) / sr
        print(f" -> Turn {idx+1} synthesized ({t_dur:.2f}s)")
        time.sleep(0.8)

    full_mix = np.concatenate(combined_samples)

    # Master broadcast peak normalization (-1.0 dBFS)
    max_peak = np.max(np.abs(full_mix))
    if max_peak > 0:
        full_mix = full_mix * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_delhi_reunion_argument_45s.mp3"
    sf.write(str(out_file), full_mix, target_sr)

    total_duration = len(full_mix) / target_sr
    print("\n==========================================================")
    print(f"[SUCCESS] Delhi Reunion Argument Sample Created!")
    print(f"File: {out_file}")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print("==========================================================")
    return out_file, total_duration

if __name__ == "__main__":
    build_reunion_podcast()
