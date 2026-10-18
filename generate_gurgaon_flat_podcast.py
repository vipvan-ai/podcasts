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

# 4 to 5 Minute Hinglish Dual-Host Master Episode
# Topic: The ₹2 Crore Gurgaon/NCR Flat vs. Renting, Inflation, and Life
# Characters:
# - Vipin: Deep, pragmatic, financially protective, grounding baritone (rahul_hi_conversational)
# - Ishita: Sweet, flirty, charming, teasing, aesthetic dreamer (ishita_enhi_companion)
EPISODE_SCRIPT = [
    {
        "turn": 1,
        "speaker": "Ishita",
        "voice": "ishita_enhi_companion",
        "pitch": 0.12,
        "pace": 0.94,
        "text": "विपिन... सुनो ना! कल शाम को जब हम गोल्फ कोर्स रोड से निकल रहे थे, तुमने वो नया हाई-राइज टॉवर देखा? क्या गजब की बालकनी थी उसकी! इमेजिन करो, 24th फ्लोर, शाम की चाय, और हाथ में तुम्हारा हाथ... कितना रोमांटिक होगा ना?"
    },
    {
        "turn": 2,
        "speaker": "Vipin",
        "voice": "rahul_hi_conversational",
        "pitch": -0.40,
        "pace": 0.95,
        "text": "रोमांटिक तो बहुत होगा इशिता... लेकिन क्या तुम्हें पता है उस 24th फ्लोर की बालकनी का प्राइस टैग क्या है? ढाई करोड़ रुपये! 2.5 Crores! और ऊपर से रजिस्ट्रेशन, क्लब चार्ज, और इंटीरियर्स अलग से। चाय का एक कप भी गले से नीचे नहीं उतरेगा जब दिमाग में दो लाख की ईएमआई घूमेगी।"
    },
    {
        "turn": 3,
        "speaker": "Ishita",
        "voice": "ishita_enhi_companion",
        "pitch": 0.12,
        "pace": 0.94,
        "text": "उफ विपिन! तुम ना हर खूबसूरत सपने का बजट शीट बना देते हो! अरे बाबा, लाइफ में थोड़ी सी एम्बिशन भी तो होनी चाहिए ना? हमारे सारे फ्रेंड्स गुड़गांव और नोएडा में 3 BHK बुक करा रहे हैं। रोहित और स्नेहा ने भी तो लिया है! हम कब तक इस रेंटेड अपार्टमेंट में दूसरों की दीवारों पर कील ठोकने से पहले लैंडलॉर्ड की परमिशन मांगते रहेंगे?"
    },
    {
        "turn": 4,
        "speaker": "Vipin",
        "voice": "rahul_hi_conversational",
        "pitch": -0.40,
        "pace": 0.95,
        "text": "इशिता, मेरी जान, रोहित और स्नेहा की मंथली ईएमआई पौने दो लाख रुपये है। वो दोनों हफ्ते में सत्तर घंटे काम कर रहे हैं सिर्फ उस कंक्रीट के डिब्बे की किश्त भरने के लिए! कभी उनके चेहरे देखे हैं? डार्क सर्कल्स और स्ट्रेस! क्या तुम्हें वो जिंदगी चाहिए? कि हम तीस साल तक बैंक के बंधुआ मजदूर बन जाएं?"
    },
    {
        "turn": 5,
        "speaker": "Ishita",
        "voice": "ishita_enhi_companion",
        "pitch": 0.14,
        "pace": 0.93,
        "text": "पर विपिन... तुम इन्फ्लेशन भी तो देखो! आज जो फ्लैट दो करोड़ का है, पांच साल बाद वो चार करोड़ का हो जाएगा। तब हम क्या करेंगे? और रेंट भी तो हर साल दस परसेंट बढ़ जाता है! लैंडलॉर्ड का जब मन करता है, बोल देता है खाली कर दो। एक लड़की के लिए अपना खुद का घर होना... एक इमोशन होता है, एक सिक्योरिटी होती है। तुम समझ क्यों नहीं रहे?"
    },
    {
        "turn": 6,
        "speaker": "Vipin",
        "voice": "rahul_hi_conversational",
        "pitch": -0.40,
        "pace": 0.94,
        "text": "मैं समझ रहा हूँ इशिता, और तुम्हारी उस सिक्योरिटी की बहुत कद्र करता हूँ। लेकिन असली सिक्योरिटी बैंक बैलेंस और मेंटल पीस में होती है, न कि करोड़ों के कर्ज में। अगर हम 50 लाख का डाउन पेमेंट म्यूचुअल फंड्स और इक्विटी में रखें, तो वो हमें दस साल में फाइनेंशियली फ्री कर देगा। लेकिन अगर हमने वो पैसा सीमेंट और ईंटों में फंसा दिया, तो अगले तीस साल हम एक दिन की छुट्टी लेने से भी डरेंगे।"
    },
    {
        "turn": 7,
        "speaker": "Ishita",
        "voice": "ishita_enhi_companion",
        "pitch": 0.15,
        "pace": 0.93,
        "text": "हम्म... बात तो तुम्हारी लॉजिकल है। लेकिन मिस्टर चार्टर्ड अकाउंटेंट... ये बताओ, अगर हम फ्लैट नहीं ले रहे, तो उस पचास लाख की सेविंग्स से मुझे पेरिस और स्विट्जरलैंड कब घुमाने ले जा रहे हो? या वो भी तुम्हारे किसी म्यूचुअल फंड कैलकुलेटर में लॉक रहेगा?"
    },
    {
        "turn": 8,
        "speaker": "Vipin",
        "voice": "rahul_hi_conversational",
        "pitch": -0.40,
        "pace": 0.95,
        "text": "हाहाहा! बिल्कुल ले जाऊंगा! यूरोप ट्रिप का बजट दो करोड़ की ईएमआई से दस गुना कम है। साल में दो इंटरनेशनल वेकेशन्स, अच्छे रेस्टोरेंट्स में डिनर, और जब मन करे शहर बदलने की आजादी... ये है असली लग्जरी। पचास लाख की ईंटों की दीवारें नहीं।"
    },
    {
        "turn": 9,
        "speaker": "Ishita",
        "voice": "ishita_enhi_companion",
        "pitch": 0.12,
        "pace": 0.93,
        "text": "अच्छा जी? तो डील पक्की समझूँ? यानी अगले महीने हम यूरोप की टिकट्स प्लान कर रहे हैं, और वो भी बिजनेस क्लास में! अगर तुमने अपनी कैलकुलेशन से पलटने की कोशिश की ना, तो मैं खुद जाकर उस दो करोड़ वाले फ्लैट का ब्रोशर तुम्हारे तकिए के नीचे रख दूंगी!"
    },
    {
        "turn": 10,
        "speaker": "Vipin",
        "voice": "rahul_hi_conversational",
        "pitch": -0.40,
        "pace": 0.95,
        "text": "अरे नहीं बाबा! ब्रोशर दूर ही रखो! पेरिस मंजूर है, लेकिन बैंक का लोन नहीं। तो चलो दोस्तों, आप कमेंट्स में बताइए—क्या दो करोड़ का फ्लैट लेना सच में प्राइड है या फिर मिडिल क्लास का सबसे बड़ा ईएमआई ट्रैप? मिलते हैं अगले एपिसोड में, ख्याल रखिए अपना!"
    }
]

def apply_deep_baritone_eq(samples, sample_rate=24000):
    # Proximity warm low-shelf boost at 125Hz (+3.5 dB) for deep chest resonance
    f0 = 125.0
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
        "loudness": 1.05,
        "speech_sample_rate": 24000,
        "enable_preprocessing": True,
        "model": "bulbul:v4-flash"
    }
    
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
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

def build_full_episode():
    print("==========================================================")
    print("Synthesizing Full Master Episode (4-5 mins) via Bulbul:v4-flash")
    print("Topic: ₹2 Crore Flat, Renting, Inflation & Dreams")
    print("Hosts: Vipin (Deep Baritone) & Ishita (Sweet, Flirty, Teasing)")
    print("==========================================================")

    target_sr = 24000
    combined_samples = []
    # 420ms natural conversational pause
    pause_samples = int(target_sr * 0.42)

    b_hp, a_hp = signal.butter(2, 75 / (target_sr / 2), btype='high')

    total_turns = len(EPISODE_SCRIPT)
    total_chars = sum(len(t["text"]) for t in EPISODE_SCRIPT)
    print(f"Total script characters: {total_chars} chars across {total_turns} turns.")
    print(f"Estimated Sarvam credits to consume: ~{total_chars * 0.002:.2f} credits (₹{total_chars * 0.002:.2f})\n")

    for idx, turn_data in enumerate(EPISODE_SCRIPT):
        turn_num = turn_data["turn"]
        speaker = turn_data["speaker"]
        voice = turn_data["voice"]
        pitch = turn_data["pitch"]
        pace = turn_data["pace"]
        text = turn_data["text"]

        print(f"[{turn_num}/{total_turns}] {speaker} ({voice}) [pitch={pitch}, pace={pace}]...")
        wav_bytes = synthesize_turn(text, voice, pitch, pace)

        raw_samples, sr = sf.read(io.BytesIO(wav_bytes))
        if sr != target_sr:
            num_samples = int(len(raw_samples) * target_sr / sr)
            raw_samples = signal.resample(raw_samples, num_samples)
            sr = target_sr

        samples = raw_samples.astype(np.float32)
        samples -= np.mean(samples)
        samples = signal.filtfilt(b_hp, a_hp, samples)

        # Apply deep chest resonance EQ for Vipin
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
        if idx < total_turns - 1:
            combined_samples.append(np.zeros(pause_samples, dtype=np.float32))

        duration_turn = len(samples) / sr
        print(f" -> Turn {turn_num} synthesized successfully ({duration_turn:.2f}s)")
        time.sleep(1.2)

    full_mix = np.concatenate(combined_samples)

    # Master broadcast peak normalization (-1.0 dBFS)
    max_peak = np.max(np.abs(full_mix))
    if max_peak > 0:
        full_mix = full_mix * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_gurgaon_flat_podcast_master_4min.mp3"
    sf.write(str(out_file), full_mix, target_sr)

    total_duration = len(full_mix) / target_sr
    minutes = int(total_duration // 60)
    seconds = int(total_duration % 60)

    print("\n==========================================================")
    print(f" [SUCCESS] Master Episode Created!")
    print(f" Output File: {out_file}")
    print(f" Total Duration: {total_duration:.2f} seconds ({minutes}m {seconds}s)")
    print(f" Credits Consumed: ~{total_chars * 0.002:.2f} credits")
    print("==========================================================")
    return out_file, total_duration

if __name__ == "__main__":
    build_full_episode()
