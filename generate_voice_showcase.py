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

# Curated Top 6 Voice Personas for Indian Podcasts
SHOWCASE_VOICES = [
    {
        "id": "ishita_enhi_companion",
        "gender": "Female",
        "name": "Ishita (Companion / Alluring)",
        "pitch": 0.12,
        "pace": 0.95,
        "text": "नमस्ते! मैं हूँ इशिता। क्या आपको भी देर रात दिल्ली की सड़कों पर ड्राइव करना और हल्की बातें करना पसंद है?"
    },
    {
        "id": "sanchita_hi_romantic",
        "gender": "Female",
        "name": "Sanchita (Romantic / Soft)",
        "pitch": 0.10,
        "pace": 0.93,
        "text": "हेलो, मैं संचिता। कुछ बातें शब्दों से नहीं, दिल की गहराइयों और खामोशी से महसूस की जाती हैं।"
    },
    {
        "id": "simran_hi_latenight",
        "gender": "Female",
        "name": "Simran (Late-Night Radio)",
        "pitch": 0.05,
        "pace": 0.94,
        "text": "गुड इवनिंग, मैं सिमरन। रात के इस शांत पहर में, अपनी पसंदीदा कॉफी के साथ हमारे साथ जुड़िए।"
    },
    {
        "id": "rahul_hi_conversational",
        "gender": "Male",
        "name": "Rahul (Deep Baritone / Pragmatic)",
        "pitch": -0.35,
        "pace": 0.95,
        "text": "नमस्ते दोस्तों, मैं हूँ राहुल। जिंदगी में सपने देखना अच्छी बात है, लेकिन उन सपनों का हिसाब-किताब भी जरूरी है।"
    },
    {
        "id": "ratan_hi_latenight_warm",
        "gender": "Male",
        "name": "Ratan (Warm Storyteller)",
        "pitch": -0.25,
        "pace": 0.93,
        "text": "नमस्कार, मैं रतन। हर शहर के पास सुनाने के लिए अपनी कुछ अनकही कहानियां होती हैं, चलिए आज एक किस्सा सुनते हैं।"
    },
    {
        "id": "shubh_enhi_companion",
        "gender": "Male",
        "name": "Shubh (Urban Hinglish / Energetic)",
        "pitch": -0.10,
        "pace": 1.00,
        "text": "हे गाइज, दिस इज शुभ! लाइफ बहुत छोटी है फालतू स्ट्रेस लेने के लिए, तो थोड़ा चिल करो और मजे करो यार!"
    }
]

def synthesize_showcase_voice(text: str, speaker_id: str, pitch: float, pace: float) -> bytes:
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": [text],
        "target_language_code": "hi-IN",
        "speaker": speaker_id,
        "pitch": pitch,
        "pace": pace,
        "loudness": 1.05,
        "speech_sample_rate": 24000,
        "enable_preprocessing": True,
        "model": "bulbul:v4-flash"
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Sarvam API error for {speaker_id}: {resp.text}")
    
    data = resp.json()
    b64_audio = data["audios"][0]
    return base64.b64decode(b64_audio)

def build_voice_showcase():
    print("==========================================================")
    print("Synthesizing Sarvam Bulbul:v4-flash Voice Showcase Reel")
    print("==========================================================")

    target_sr = 24000
    combined_audio = []
    gap_samples = int(target_sr * 0.70) # 700ms distinct gap between voice samples
    b_hp, a_hp = signal.butter(2, 75 / (target_sr / 2), btype='high')

    total_chars = sum(len(item["text"]) for item in SHOWCASE_VOICES)
    print(f"Total characters: {total_chars} chars across {len(SHOWCASE_VOICES)} voices.")
    print(f"Estimated credits: ~{total_chars * 0.002:.2f} credits (less than ₹1.20)\n")

    individual_files = []

    for idx, item in enumerate(SHOWCASE_VOICES):
        v_id = item["id"]
        v_name = item["name"]
        pitch = item["pitch"]
        pace = item["pace"]
        text = item["text"]

        print(f"[{idx+1}/{len(SHOWCASE_VOICES)}] Synthesizing {v_name} ({v_id})...")
        wav_bytes = synthesize_showcase_voice(text, v_id, pitch, pace)

        raw_samples, sr = sf.read(io.BytesIO(wav_bytes))
        if sr != target_sr:
            num_samples = int(len(raw_samples) * target_sr / sr)
            raw_samples = signal.resample(raw_samples, num_samples)
            sr = target_sr

        samples = raw_samples.astype(np.float32)
        samples -= np.mean(samples)
        samples = signal.filtfilt(b_hp, a_hp, samples)

        # 20ms Cosine Envelope
        fade_len = int(sr * 0.02)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        # Peak normalize each sample
        p_max = np.max(np.abs(samples))
        if p_max > 0:
            samples = samples * (0.891 / p_max)

        # Save individual voice preview file as well
        single_path = AUDIO_DIR / f"preview_{v_id}.mp3"
        sf.write(str(single_path), samples, target_sr)
        individual_files.append((v_name, single_path))

        combined_audio.append(samples)
        if idx < len(SHOWCASE_VOICES) - 1:
            combined_audio.append(np.zeros(gap_samples, dtype=np.float32))

        print(f" -> Done: {len(samples)/sr:.2f}s (saved to {single_path.name})")
        time.sleep(1)

    full_reel = np.concatenate(combined_audio)
    reel_path = AUDIO_DIR / "sarvam_v4_voices_showcase_reel.mp3"
    sf.write(str(reel_path), full_reel, target_sr)

    total_sec = len(full_reel) / target_sr
    print("\n==========================================================")
    print(f" [COMPLETE] Voice Showcase Reel Created!")
    print(f" Master Reel: {reel_path}")
    print(f" Total Duration: {total_sec:.2f} seconds")
    print("==========================================================")
    return reel_path, individual_files

if __name__ == "__main__":
    build_voice_showcase()
