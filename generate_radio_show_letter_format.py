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

# Radio Show Format Episode:
# Show Name: "Dil Ki Baatein with Sanket & Ishita"
# Format: Professional Radio Intro -> Viewer Letter Reading -> Personal Family Examples -> Societal Impact & Outro
# Hosts:
# - Sanket: ratan_hi_latenight_warm (warm, reflective, radio host)
# - Ishita: sanchita_hi_romantic (sweet, empathetic, engaging co-host)
RADIO_SHOW_SCRIPT = [
    {
        "turn": 1,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.22,
        "pace": 0.95,
        "text": "नमस्कार दोस्तों! 'दिल की बातें' के आज के इस खास एपिसोड में आपका स्वागत है। मैं हूँ आपका दोस्त संकेत, और मेरे साथ हमेशा की तरह मौजूद हैं बेहद खूबसूरत आवाज की मल्लिका, इशिता!"
    },
    {
        "turn": 2,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.12,
        "pace": 0.94,
        "text": "हेलो एवरीवन! थैंक यू सो मच संकेत... आज का हमारा शो बहुत ही पर्सनल और इमोशनल होने वाला है। आज सुबह जब हम हमारे लिसनर्स के ईमेल्स देख रहे थे, तो बेंगलुरु से हमारे एक लिस्नर, राहुल की चिट्ठी ने हमारा दिल छू लिया।"
    },
    {
        "turn": 3,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.25,
        "pace": 0.93,
        "text": "बिल्कुल इशिता। राहुल लिखते हैं—'संकेत भाई और इशिता जी, मैं पिछले तीन साल से एक आईटी कंपनी में अस्सी-अस्सी घंटे काम कर रहा हूँ। पिछले हफ्ते मेरी माँ की तबीयत अचानक बिगड़ी, और मैं अस्पताल जाने के बजाय क्लाइंट की कॉल पर म्यूट होकर रो रहा था। समझ नहीं आ रहा कि ये पैकेज कमाकर मैं किसे खुश कर रहा हूँ?'"
    },
    {
        "turn": 4,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.10,
        "pace": 0.93,
        "text": "ओह गॉड... ये सुनकर सच में रोंगटे खड़े हो जाते हैं। और पता है संकेत, ये सिर्फ राहुल की कहानी नहीं है। मेरे अपने बड़े भाई को देखो! पिछले साल जब घर में दिवाली का त्योहार था, सब लोग आँगन में दीये जला रहे थे... और भैया अपने कमरे का दरवाजा बंद करके लंदन की क्लाइंट मीटिंग अटेंड कर रहे थे। माँ आँसू पोंछते हुए बस उनके कमरे के दरवाजे को देख रही थीं।"
    },
    {
        "turn": 5,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.25,
        "pace": 0.94,
        "text": "इशिता, मेरी फैमिली में भी यही हुआ। मेरे कजिन ने स्टार्टअप में फंडिंग मिलने के बाद दिन-रात एक कर दिया। चौंतीस साल की उम्र में उसे हाई बीपी और पैनिक अटैक्स आने लगे। जब डॉक्टर ने बोला कि अगर काम नहीं छोड़ा तो कभी रिकवर नहीं कर पाओगे, तब जाकर पूरे परिवार की आँखें खुलीं। हमने सोसायटी में ये कैसा माहौल बना दिया है जहां बर्नआउट को मेडल की तरह दिखाया जाता है?"
    },
    {
        "turn": 6,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.12,
        "pace": 0.93,
        "text": "यही तो सबसे कड़वा सच है संकेत। हम अपनी जवानी, अपने रिश्ते, और अपने पेरेंट्स का वो कीमती वक्त उन कंपनियों को बेच रहे हैं, जो कल हमारी जगह किसी और को हायर करने में चौबीस घंटे भी नहीं लगाएंगी। एम्बिशन होना बहुत अच्छी बात है, लेकिन खुद को खोकर नहीं।"
    },
    {
        "turn": 7,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.22,
        "pace": 0.95,
        "text": "बिल्कुल सही कहा इशिता। तो जितने भी दोस्त इस वक्त हमें अपनी कारों में, हेडफोन्स पर या घर पर सुन रहे हैं... आज अपने काम से थोड़ा ब्रेक लीजिए, अपने परिवार के पास बैठिए और एक कप चाय साथ पीजिए। आप राहुल की इस चिट्ठी पर क्या सोचते हैं, हमें नीचे कमेंट्स में जरूर बताइए। मैं संकेत, और मेरी प्यारी को-होस्ट इशिता... अब लेते हैं आपसे विदा, अपना बहुत ख्याल रखिए!"
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
    
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=40)
            if resp.status_code == 200:
                data = resp.json()
                b64_audio = data["audios"][0]
                return base64.b64decode(b64_audio)
            else:
                print(f"    [Retry {attempt+1}] Sarvam status {resp.status_code}: {resp.text}")
                time.sleep(2)
        except Exception as e:
            print(f"    [Retry {attempt+1}] Request error: {e}")
            time.sleep(2)
            
    raise RuntimeError(f"Failed to synthesize turn after 3 attempts.")

def build_radio_show_sample():
    print("==========================================================")
    print("Synthesizing Full Radio Show Episode: Sanket & Ishita")
    print("Format: Radio Intro -> Viewer Letter -> Family Stories -> Society Impact")
    print("==========================================================")

    target_sr = 24000
    combined_audio = []
    # 450ms natural unhurried radio pause between turns
    pause_samples = int(target_sr * 0.45)
    b_hp, a_hp = signal.butter(2, 75 / (target_sr / 2), btype='high')

    total_chars = sum(len(t["text"]) for t in RADIO_SHOW_SCRIPT)
    print(f"Total script characters: {total_chars} chars across {len(RADIO_SHOW_SCRIPT)} turns.")
    print(f"Estimated credits: ~{total_chars * 0.002:.2f} credits (around ₹3.80)\n")

    for idx, turn_data in enumerate(RADIO_SHOW_SCRIPT):
        turn_num = turn_data["turn"]
        speaker = turn_data["speaker"]
        voice = turn_data["voice"]
        pitch = turn_data["pitch"]
        pace = turn_data["pace"]
        text = turn_data["text"]

        print(f"[{turn_num}/{len(RADIO_SHOW_SCRIPT)}] {speaker} ({voice})...")
        wav_bytes = synthesize_turn(text, voice, pitch, pace)

        raw_samples, sr = sf.read(io.BytesIO(wav_bytes))
        if sr != target_sr:
            num_samples = int(len(raw_samples) * target_sr / sr)
            raw_samples = signal.resample(raw_samples, num_samples)
            sr = target_sr

        samples = raw_samples.astype(np.float32)
        samples -= np.mean(samples)
        samples = signal.filtfilt(b_hp, a_hp, samples)

        # 20ms Smooth Cosine Fade Envelope
        fade_len = int(sr * 0.02)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        combined_audio.append(samples)
        if idx < len(RADIO_SHOW_SCRIPT) - 1:
            combined_audio.append(np.zeros(pause_samples, dtype=np.float32))

        t_dur = len(samples) / sr
        print(f" -> Turn {turn_num} synthesized ({t_dur:.2f}s)")
        time.sleep(1)

    full_mix = np.concatenate(combined_audio)

    # Master broadcast peak normalization (-1.0 dBFS)
    max_peak = np.max(np.abs(full_mix))
    if max_peak > 0:
        full_mix = full_mix * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_radio_show_viewer_letter_sanket_ishita.mp3"
    sf.write(str(out_file), full_mix, target_sr)

    total_duration = len(full_mix) / target_sr
    minutes = int(total_duration // 60)
    seconds = int(total_duration % 60)

    print("\n==========================================================")
    print(f" [SUCCESS] Radio Show Episode Created!")
    print(f" File: {out_file}")
    print(f" Duration: {total_duration:.2f} seconds ({minutes}m {seconds}s)")
    print(f" Credits Consumed: ~{total_chars * 0.002:.2f} credits")
    print("==========================================================")
    return out_file, total_duration

if __name__ == "__main__":
    build_radio_show_sample()
