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

# Late-Night Relaxed Hindi Dialogue (45-60s)
# Topic: 2 AM Late-Night Drives & Chai Culture
# Vipin: Deep, calm baritone
# Ishita: Sweet, soft, intimate & alluring
LATE_NIGHT_SCRIPT = [
    {
        "speaker": "Vipin",
        "voice": "rahul",
        "pitch": -0.5,
        "pace": 0.94,
        "text": "रात के ठीक दो बज रहे हैं... इंडिया गेट की चौड़ी, शांत सड़कें, कार की खिड़की से आती हल्की ठंडी हवा... और हाथ में अदरक वाली गर्म कुल्हड़ की चाय। इशिता, इस शहर का ये सुकून दिन की भागदौड़ में कहीं खो जाता है।"
    },
    {
        "speaker": "Ishita",
        "voice": "ishita",
        "pitch": 0.15,
        "pace": 0.91,
        "text": "बिल्कुल विपिन... जब पूरी दुनिया सो रही होती है, तब ये शहर अपनी असली रूह दिखाता है। और इस खामोशी में, हल्की सी धुन के साथ... जब तुम चाय की पहली चुस्की लेते हो, तो लगता है जैसे वक्त सच में ठहर गया हो।"
    },
    {
        "speaker": "Vipin",
        "voice": "rahul",
        "pitch": -0.5,
        "pace": 0.94,
        "text": "यही तो जादू है इन रातों का। दिन में जो शहर हॉर्न और ट्रैफिक के शोर में दब जाता है... रात को वही दिल्ली एक पुरानी, हसीन दास्तान जैसी लगने लगती है। कभी-कभी लगता है, ये सफर कभी खत्म ही न हो।"
    },
    {
        "speaker": "Ishita",
        "voice": "ishita",
        "pitch": 0.15,
        "pace": 0.91,
        "text": "तो फिर इस सफर को चलने दो ना... बस अगली नुक्कड़ पर एक और कुल्हड़ चाय, और ये धीमी बातचीत। कुछ रातें खत्म होने के लिए नहीं, बस महसूस करने के लिए बनी होती हैं।"
    }
]

def apply_deep_baritone_eq(samples, sample_rate=24000):
    # Proximity warm low-shelf boost at 130Hz (+3.5 dB) for deep voice
    f0 = 130.0
    Q = 0.9
    gain_db = 3.5
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / sample_rate
    alpha = np.sin(w0) / (2 * Q)
    
    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A

    b = np.array([b0, b1, b2]) / a0
    a = np.array([a0, a1, a2]) / a0
    return signal.filtfilt(b, a, samples)

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
        "loudness": 1.0,
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

def build_latenight_chai_sample():
    print("==========================================================")
    print("Generating Relaxed Late-Night Hindi Podcast Sample")
    print("Topic: 2 AM Drives & Chai (Vipin Deep & Ishita Sweet)")
    print("==========================================================")

    combined_samples = []
    target_sr = 24000
    # 450ms relaxed, unhurried inter-host pause
    pause_samples = int(target_sr * 0.45)

    b_hp, a_hp = signal.butter(2, 75 / (target_sr / 2), btype='high')

    for idx, turn in enumerate(LATE_NIGHT_SCRIPT):
        speaker = turn["speaker"]
        voice = turn["voice"]
        pitch = turn["pitch"]
        pace = turn["pace"]
        text = turn["text"]
        
        print(f"\n[Turn {idx+1}/{len(LATE_NIGHT_SCRIPT)}] {speaker} ({voice}, pitch={pitch}, pace={pace})...")
        wav_bytes = synthesize_turn(text, voice, pitch, pace)
        
        raw_samples, sr = sf.read(io.BytesIO(wav_bytes))
        if sr != target_sr:
            num_samples = int(len(raw_samples) * target_sr / sr)
            raw_samples = signal.resample(raw_samples, num_samples)
            sr = target_sr

        samples = raw_samples.astype(np.float32)
        samples -= np.mean(samples)
        samples = signal.filtfilt(b_hp, a_hp, samples)

        # Apply deep baritone enhancement for Vipin
        if speaker == "Vipin":
            samples = apply_deep_baritone_eq(samples, target_sr)

        # 20ms Smooth Cosine Envelope at edges
        fade_len = int(sr * 0.02)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        combined_samples.append(samples)
        if idx < len(LATE_NIGHT_SCRIPT) - 1:
            combined_samples.append(np.zeros(pause_samples, dtype=np.float32))

        t_dur = len(samples) / sr
        print(f" -> Turn {idx+1} synthesized ({t_dur:.2f}s)")
        time.sleep(0.8)

    full_mix = np.concatenate(combined_samples)

    # Master broadcast peak normalization (-1.0 dBFS)
    max_peak = np.max(np.abs(full_mix))
    if max_peak > 0:
        full_mix = full_mix * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_latenight_chai_relaxed_50s.mp3"
    sf.write(str(out_file), full_mix, target_sr)

    total_duration = len(full_mix) / target_sr
    print("\n==========================================================")
    print(f"[SUCCESS] Relaxed Late-Night Sample Created!")
    print(f"File: {out_file}")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print("==========================================================")
    return out_file, total_duration

if __name__ == "__main__":
    build_latenight_chai_sample()
