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

# 50-Second Master Dialogue
# Topic: Long Work Hours & Hustle Culture (70-hour work weeks vs. life & burnout)
# Characters:
# - Sanket (Male Host): ratan_hi_latenight_warm (warm, reflective, grounded)
# - Ishita (Female Host): sanchita_hi_romantic (soft, sweet, caring, teasing)
HUSTLE_SCRIPT = [
    {
        "turn": 1,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.10,
        "pace": 0.94,
        "text": "संकेत... रात के ग्यारह बज रहे हैं और तुम्हारा लैपटॉप अभी भी खुला है! ये 70 घंटे काम करने का बुखार तुम्हारे सिर से कब उतरेगा? कभी खुद के लिए भी वक्त निकालोगे या नहीं?"
    },
    {
        "turn": 2,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.25,
        "pace": 0.93,
        "text": "इशिता, बस ये लास्ट प्रेजेंटेशन खत्म कर रहा हूँ। तुम्हें पता है ना कॉर्पोरेट में सर्वाइव करना कितना टफ है? अगर वीकेंड्स और लेट नाइट्स काम नहीं करेंगे, तो वो प्रमोशन और ग्रोथ कैसे मिलेगी?"
    },
    {
        "turn": 3,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.12,
        "pace": 0.93,
        "text": "पर उस प्रमोशन का क्या फायदा संकेत, जब एंजाइटी और डार्क सर्कल्स फ्री में मिल रहे हों? जिंदगी स्क्रीन के सामने खत्म होने के लिए नहीं बनी है। कभी बालकनी में खड़े होकर ठंडी हवा और सुकून भी तो महसूस करो।"
    },
    {
        "turn": 4,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.25,
        "pace": 0.93,
        "text": "हम्म... बात तो तुम्हारी सोलह आने सच है इशिता। जब तुम इतनी फिक्र से समझाती हो ना, तो लगता है कि ये भागदौड़ सच में बेकार है। चलो, लैपटॉप बंद... अब सिर्फ चाय और तुम्हारी बातें।"
    }
]

def synthesize_turn(text: str, speaker: str, pitch: float, pace: float) -> bytes:
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": [text],
        "target_language_code": "hi-IN",
        "speaker": speaker,
        "pitch": pitch,
        "pace": pace,
        "loudness": 1.05,
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

def build_hustle_podcast_sample():
    print("==========================================================")
    print("Generating 50s Master Sample: Long Work Hours & Hustle")
    print("Characters: Sanket (Ratan voice) & Ishita (Sanchita voice)")
    print("==========================================================")

    target_sr = 24000
    combined_audio = []
    pause_samples = int(target_sr * 0.40) # 400ms natural conversational pause
    b_hp, a_hp = signal.butter(2, 75 / (target_sr / 2), btype='high')

    total_chars = sum(len(t["text"]) for t in HUSTLE_SCRIPT)
    print(f"Total script characters: {total_chars} chars across 4 turns.")
    print(f"Estimated credits: ~{total_chars * 0.002:.2f} credits (around ₹1.25)\n")

    for idx, turn in enumerate(HUSTLE_SCRIPT):
        turn_num = turn["turn"]
        speaker = turn["speaker"]
        voice = turn["voice"]
        pitch = turn["pitch"]
        pace = turn["pace"]
        text = turn["text"]

        print(f"[{turn_num}/4] {speaker} ({voice})...")
        wav_bytes = synthesize_turn(text, voice, pitch, pace)

        raw_samples, sr = sf.read(io.BytesIO(wav_bytes))
        if sr != target_sr:
            num_samples = int(len(raw_samples) * target_sr / sr)
            raw_samples = signal.resample(raw_samples, num_samples)
            sr = target_sr

        samples = raw_samples.astype(np.float32)
        samples -= np.mean(samples)
        samples = signal.filtfilt(b_hp, a_hp, samples)

        # 20ms Smooth Cosine Envelope at edges
        fade_len = int(sr * 0.02)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        combined_audio.append(samples)
        if idx < len(HUSTLE_SCRIPT) - 1:
            combined_audio.append(np.zeros(pause_samples, dtype=np.float32))

        t_dur = len(samples) / sr
        print(f" -> Turn {turn_num} synthesized ({t_dur:.2f}s)")
        time.sleep(1)

    full_mix = np.concatenate(combined_audio)

    # Broadcast peak normalization (-1.0 dBFS)
    max_peak = np.max(np.abs(full_mix))
    if max_peak > 0:
        full_mix = full_mix * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_hustle_work_hours_sanket_ishita_50s.mp3"
    sf.write(str(out_file), full_mix, target_sr)

    total_duration = len(full_mix) / target_sr
    print("\n==========================================================")
    print(f" [SUCCESS] Master Episode Created!")
    print(f" File: {out_file}")
    print(f" Total Duration: {total_duration:.2f} seconds")
    print(f" Credits Consumed: ~{total_chars * 0.002:.2f} credits")
    print("==========================================================")
    return out_file, total_duration

if __name__ == "__main__":
    build_hustle_podcast_sample()
