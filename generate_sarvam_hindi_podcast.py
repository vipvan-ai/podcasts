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

# Conversational Hindi Podcast Dialogue: "Will AI Glasses replace Smartphones?"
# Co-hosts: Shubh (Male) & Ishita (Female)
PODCAST_TURNS = [
    {
        "speaker": "Shubh",
        "voice": "shubh",
        "text": "नमस्ते दोस्तों! फ्यूचर ह्यूमन डेली के इस खास एपिसोड में आपका स्वागत है। ज़रा सोचिए, अगर आपकी जेब में रखा भारी-भरकम स्मार्टफोन हमेशा के लिए गायब हो जाए, और उसकी जगह सिर्फ एक हल्का-फुल्का स्टाइलिश चश्मा आ जाए? आज हम बात कर रहे हैं AI स्मार्ट ग्लासेस की।"
    },
    {
        "speaker": "Ishita",
        "voice": "ishita",
        "text": "बिल्कुल शुभ! और सोचिए कितना मजेदार होगा जब आपको बार-बार स्क्रीन अनलॉक करने की जरूरत ही नहीं पड़ेगी। आप बस सड़क पर चलते हुए किसी खूबसूरत इमारत या गाड़ी को देखते हैं, और AI सीधे आपकी आंखों के सामने उसकी पूरी डिटेल बता देता है!"
    },
    {
        "speaker": "Shubh",
        "voice": "shubh",
        "text": "सुनने में तो ये बिल्कुल किसी साइंस फिक्शन फिल्म जैसा लगता है, इशिता! लेकिन असली पहेली ये है—क्या लोग दिनभर अपने चेहरे पर कैमरा और माइक पहनकर घूमने में कंफर्टेबल होंगे? हमारी प्राइवेसी का क्या होगा?"
    },
    {
        "speaker": "Ishita",
        "voice": "ishita",
        "text": "यही तो सबसे बड़ा पेच है, शुभ! सुविधा जितनी जादुई लगती है, हमारी पर्सनल लाइफ पर उसका असर उतना ही बड़ा हो सकता है। तो चलिए, आज इसी दिलचस्प बहस की तह तक जाते हैं!"
    }
]

def synthesize_sarvam_turn(text: str, speaker: str) -> bytes:
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
        "pace": 1.0,
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

def build_sarvam_podcast_sample():
    print("==========================================================")
    print("Synthesizing Master Hindi Podcast Sample with Sarvam Bulbul:v3")
    print("Hosts: Shubh (Male) & Ishita (Female)")
    print("Topic: Will AI Glasses Replace Smartphones?")
    print("==========================================================")
    
    combined_samples = []
    target_sr = 24000
    pause_samples = int(target_sr * 0.40) # 400ms natural conversational pause

    b_hp, a_hp = signal.butter(2, 80 / (target_sr / 2), btype='high')

    for idx, turn in enumerate(PODCAST_TURNS):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        
        print(f"\n[Turn {idx+1}/{len(PODCAST_TURNS)}] Synthesizing {speaker} (Voice: {voice})...")
        wav_bytes = synthesize_sarvam_turn(text, voice)
        
        # Read WAV bytes
        raw_samples, sr = sf.read(io.BytesIO(wav_bytes))
        if sr != target_sr:
            # Resample if needed
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
        if idx < len(PODCAST_TURNS) - 1:
            combined_samples.append(np.zeros(pause_samples, dtype=np.float32))

        duration_turn = len(samples) / sr
        print(f" -> Successfully synthesized Turn {idx+1} ({duration_turn:.2f}s)")
        time.sleep(1)

    full_mix = np.concatenate(combined_samples)

    # Master broadcast peak normalization (-1.0 dBFS)
    max_peak = np.max(np.abs(full_mix))
    if max_peak > 0:
        full_mix = full_mix * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_sarvam_hindi_podcast_45s.mp3"
    sf.write(str(out_file), full_mix, target_sr)

    total_duration = len(full_mix) / target_sr
    print("\n==========================================================")
    print(f"[SUCCESS] Sarvam AI Hindi Podcast Master Created!")
    print(f"Output File: {out_file}")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print("==========================================================")
    return out_file, total_duration

if __name__ == "__main__":
    build_sarvam_podcast_sample()
