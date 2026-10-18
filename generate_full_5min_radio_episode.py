import os
import sys
import io
import re
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
CACHE_DIR = AUDIO_DIR / "cache_5min_radio"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

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

# Full 5-6 Minute Master Broadcast Episode
# Show Name: "Dil Ki Baatein with Sanket & Ishita"
# Episode Topic: Toxic Work Hours, Burnout, 4-Day Work Weeks, and Corporate Reform
FULL_RADIO_EPISODE = [
    {
        "turn": 1,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.22,
        "pace": 0.95,
        "text": "नमस्कार दोस्तों! 'दिल की बातें' के आज के इस बेहद खास एपिसोड में आपका स्वागत है। मैं हूँ आपका दोस्त संकेत, और मेरे साथ हमेशा की तरह मौजूद हैं बेहद खूबसूरत आवाज और गहरी समझ रखने वाली हमारी प्यारी को-होस्ट, इशिता!"
    },
    {
        "turn": 2,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.12,
        "pace": 0.94,
        "text": "हेलो एवरीवन! थैंक यू सो मच संकेत... आज का हमारा शो बहुत ही पर्सनल, संजीदा और शायद हम सबकी जिंदगी से सीधा जुड़ा हुआ है। आज सुबह जब हम हमारे लिसनर्स के ईमेल्स पढ़ रहे थे, तो बेंगलुरु से हमारे एक रेगुलर लिसनर, राहुल की चिट्ठी ने हमारे दिल को अंदर तक झकझोर दिया।"
    },
    {
        "turn": 3,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.25,
        "pace": 0.93,
        "text": "बिल्कुल इशिता। राहुल ने जो लिखा, वो आज भारत के लाखों प्रोफेशनल्स का दर्द है। राहुल लिखते हैं—'संकेत भाई और इशिता जी, मैं पिछले तीन साल से एक टेक कंपनी में अस्सी-अस्सी घंटे काम कर रहा हूँ। पिछले हफ्ते मेरी माँ की तबीयत अचानक बिगड़ी, और मैं अस्पताल जाने के बजाय क्लाइंट की कॉल पर म्यूट होकर रो रहा था। समझ नहीं आ रहा कि ये पैकेज और अप्रेजल कमाकर मैं किसे खुश कर रहा हूँ?'"
    },
    {
        "turn": 4,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.10,
        "pace": 0.93,
        "text": "ओह गॉड... ये सुनकर सच में रोंगटे खड़े हो जाते हैं। और पता है संकेत, ये सिर्फ राहुल की अकेले की कहानी नहीं है। मेरे अपने बड़े भाई को देखो! पिछले साल जब घर में दिवाली का पावन त्योहार था, सब लोग आँगन में दीये जला रहे थे... और भैया अपने कमरे का दरवाजा बंद करके लंदन की क्लाइंट मीटिंग अटेंड कर रहे थे। माँ आँसू पोंछते हुए बस उनके कमरे के दरवाजे को देख रही थीं कि काश उनका बेटा दो मिनट आकर आरती में शामिल हो जाए।"
    },
    {
        "turn": 5,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.25,
        "pace": 0.94,
        "text": "इशिता, मेरी फैमिली में भी बिल्कुल यही हुआ। मेरे कजिन ने जब अपना स्टार्टअप शुरू किया, तो उसने दिन-रात एक कर दिया। चौंतीस साल की छोटी सी उम्र में उसे हाई बीपी और पैनिक अटैक्स आने लगे। जब डॉक्टर ने साफ कह दिया कि अगर अगले एक महीने तुमने काम बंद नहीं किया, तो शायद तुम कभी नॉर्मल जिंदगी नहीं जी पाओगे, तब जाकर पूरे परिवार की आँखें खुलीं। हमने हमारे समाज में ये कैसा माहौल बना दिया है जहां बर्नआउट और नींद न लेने को किसी बहादुरी के मेडल की तरह दिखाया जाता है?"
    },
    {
        "turn": 6,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.12,
        "pace": 0.93,
        "text": "यही तो सबसे कड़वा सच है संकेत। असलियत ये है कि हमारे ऑफिसेज में एक टॉक्सिक कल्चर बन चुका है—'प्रेजेंटीइज्म' का कल्चर! यानी अगर आप रात को दस बजे भी ऑफिस की स्लैक और व्हाट्सएप पर एक्टिव नहीं हैं, तो बॉस सोचने लगता है कि आप सीरियस नहीं हैं। वीकेंड्स पर एक ईमेल का रिप्लाई न करो, तो मंडे सुबह मीटिंग में इनडायरेक्ट ताने मारे जाते हैं। हम अपनी जवानी और अपनों का वो कीमती वक्त उन कंपनियों को बेच रहे हैं, जो कल हमारी जगह किसी और को हायर करने में चौबीस घंटे भी नहीं लगाएंगी।"
    },
    {
        "turn": 7,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.24,
        "pace": 0.94,
        "text": "बिल्कुल सही बात है इशिता। और सबसे बड़ा सवाल ये है कि क्या इतने लंबे घंटों से असल में प्रोडक्टिविटी बढ़ती है? साइंस और डेटा तो इसके बिल्कुल उलट कहते हैं! जब एक इंसान दिन में बारह घंटे स्क्रीन घूरता है, तो शुरुआत के चार घंटे के बाद उसका दिमाग सिर्फ गलतियां करता है। दुनिया के कई विकसित देश—जैसे यूके, जर्मनी और जापान की कई कंपनियां अब फोर-डे वर्क वीक, यानी चार दिन काम और तीन दिन की छुट्टी के मॉडल पर काम कर रही हैं। और रिजल्ट्स? कर्मचारियों की प्रोडक्टिविटी पैंतीस परसेंट बढ़ गई और सिक लीव्स आधी हो गईं!"
    },
    {
        "turn": 8,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.11,
        "pace": 0.94,
        "text": "एग्जैक्टली संकेत! और हमारे भारत में अभी भी सत्तर घंटे काम करने की वकालत की जाती है। हमें अपने कॉर्पोरेट्स में माइंडसेट बदलना होगा। सबसे पहले हमारे ऑफिसेज में 'राइट टू डिस्कनेक्ट' का कानून आना चाहिए—कि शाम सात बजे के बाद न तो कोई ऑफिशियल कॉल आएगी, और न ही वीकेंड्स पर काम का प्रेशर होगा। यूरोप के कई देशों में तो कानूनन शाम के बाद एम्प्लॉई को ईमेल भेजना ही गैर-कानूनी है!"
    },
    {
        "turn": 9,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.24,
        "pace": 0.94,
        "text": "और ये जिम्मेदारी सिर्फ सरकार की नहीं है, कॉर्पोरेट लीडर्स, फाउंडर्स और एचआर मैनेजर्स की भी है। आपको किसी एम्प्लॉई की वैल्यू इस बात से नहीं आंकनी चाहिए कि वो कुर्सी पर कितने घंटे चिपका रहा, बल्कि इस बात से आंकनी चाहिए कि उसने काम क्या डिलीवर किया। अगर कोई इंसान अपना काम पांच घंटे में खत्म करके घर जा रहा है, तो वो एफिशिएंट है, कामचोर नहीं!"
    },
    {
        "turn": 10,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.12,
        "pace": 0.93,
        "text": "लेकिन संकेत, जब तक सिस्टम नहीं बदलता, तब तक हमारे जैसे आम एम्प्लॉईज क्या करें? क्योंकि सबको अपनी नौकरी और ईएमआई की फिक्र होती है। हम अपनी बाउंड्रीज कैसे सेट करें?"
    },
    {
        "turn": 11,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.25,
        "pace": 0.94,
        "text": "बहुत ही प्रैक्टिकल सवाल पूछा तुमने इशिता। पहली चीज—'ना' कहना सीखिए, लेकिन पोलाइटली और प्रोफेशनली। जब काम खत्म हो, तो लैपटॉप शटडाउन कीजिए। हर व्हाट्सएप मैसेज का जवाब उसी सेकंड देना बंद कीजिए, वरना लोग आपकी अनअवेलेबिलिटी की इज्जत करना कभी नहीं सीखेंगे। और दूसरी बात—ऑफिस से बाहर अपनी एक पहचान बनाइए। कोई हॉबी, जिम, शाम की वॉक, या दोस्तों के साथ बैठना। जब आपकी जिंदगी में काम के अलावा भी कुछ होगा, तो ऑफिस का स्ट्रेस आपको कभी तोड़ नहीं पाएगा।"
    },
    {
        "turn": 12,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.12,
        "pace": 0.93,
        "text": "कितनी खूबसूरत बात कही तुमने संकेत... 'ऑफिस से बाहर अपनी पहचान बनाइए।' याद रखिए दोस्तों, कंपनी के नोटिस बोर्ड पर आपका डेजिग्नेशन लिखा हो सकता है, लेकिन घर की दहलीज पर आप किसी के बेटे हैं, किसी की बेटी, किसी के जीवनसाथी या माता-पिता। वो कंपनी एक दिन आपका रिप्लेसमेंट ढूंढ लेगी, लेकिन आपके अपने कभी आपका रिप्लेसमेंट नहीं ढूंढ पाएंगे।"
    },
    {
        "turn": 13,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.22,
        "pace": 0.95,
        "text": "तो जितने भी दोस्त इस वक्त हमें अपनी कारों में, ट्रैफिक में, या हेडफोन्स पर सुन रहे हैं... आज अगर आप ऑफिस में बैठे हैं, तो घड़ी देखिए, काम को कल के लिए रोकिए और अपने घर जाइए। अपने माता-पिता के पैर छुइए, अपने पार्टनर के साथ बैठकर चाय की चुस्की लीजिए और बच्चों की वो प्यारी सी मुस्कान देखिए।"
    },
    {
        "turn": 14,
        "speaker": "Ishita",
        "voice": "sanchita_hi_romantic",
        "pitch": 0.12,
        "pace": 0.94,
        "text": "और हाँ, आप राहुल की इस चिट्ठी और हमारे इस डिस्कशन पर क्या सोचते हैं? क्या आपके ऑफिस में भी ऐसा प्रेशर है? हमें नीचे कमेंट्स में लिखकर जरूर बताइए। हम आपके हर एक कमेंट को पढ़ते हैं।"
    },
    {
        "turn": 15,
        "speaker": "Sanket",
        "voice": "ratan_hi_latenight_warm",
        "pitch": -0.22,
        "pace": 0.95,
        "text": "मैं संकेत, और मेरी बेहद अज़ीज़ को-होस्ट इशिता... अब लेते हैं 'दिल की बातें' के इस एपिसोड से आपसे विदा। जिंदगी बहुत खूबसूरत है, इसे खुलकर जीजिए। शुभ रात्रि, शब्बा खैर, और अपना बहुत ख्याल रखिए!"
    }
]

def split_text_into_chunks(text, max_chars=450):
    sentences = re.split(r'([।!?]+)', text)
    chunks = []
    current = ""
    for i in range(0, len(sentences), 2):
        s = sentences[i]
        punc = sentences[i+1] if i+1 < len(sentences) else ""
        full_sentence = s + punc
        if len(current) + len(full_sentence) <= max_chars:
            current += full_sentence
        else:
            if current.strip():
                chunks.append(current.strip())
            current = full_sentence
    if current.strip():
        chunks.append(current.strip())
    return chunks

def synthesize_chunk(text_chunk: str, speaker: str, pitch: float, pace: float) -> bytes:
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": [text_chunk],
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
            
    raise RuntimeError(f"Failed to synthesize chunk after 3 attempts.")

def synthesize_turn_cached(turn_data, target_sr=24000):
    turn_num = turn_data["turn"]
    speaker = turn_data["speaker"]
    voice = turn_data["voice"]
    pitch = turn_data["pitch"]
    pace = turn_data["pace"]
    full_text = turn_data["text"]

    cache_file = CACHE_DIR / f"turn_{turn_num:02d}_{speaker}.wav"
    if cache_file.exists() and cache_file.stat().st_size > 5000:
        samples, sr = sf.read(str(cache_file))
        print(f"[{turn_num}/{len(FULL_RADIO_EPISODE)}] Loaded {speaker} from disk cache ({len(samples)/sr:.2f}s)")
        return samples

    print(f"[{turn_num}/{len(FULL_RADIO_EPISODE)}] Synthesizing {speaker} ({voice}) via API...")
    chunks = split_text_into_chunks(full_text, max_chars=450)
    chunk_samples = []

    for c_idx, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"   -> Processing sub-chunk {c_idx+1}/{len(chunks)} ({len(chunk)} chars)...")
        wav_bytes = synthesize_chunk(chunk, voice, pitch, pace)
        raw, sr = sf.read(io.BytesIO(wav_bytes))
        if sr != target_sr:
            num_samples = int(len(raw) * target_sr / sr)
            raw = signal.resample(raw, num_samples)
            sr = target_sr
        chunk_samples.append(raw.astype(np.float32))
        time.sleep(0.8)

    # Stitch sub-chunks together seamlessly with micro 120ms clause pause
    stitched = []
    micro_gap = np.zeros(int(target_sr * 0.12), dtype=np.float32)
    for c_idx, s in enumerate(chunk_samples):
        stitched.append(s)
        if c_idx < len(chunk_samples) - 1:
            stitched.append(micro_gap)

    turn_audio = np.concatenate(stitched)
    sf.write(str(cache_file), turn_audio, target_sr)
    print(f"   -> Turn {turn_num} completed and cached ({len(turn_audio)/target_sr:.2f}s)")
    return turn_audio

def build_full_5min_radio_episode():
    print("==========================================================")
    print("Synthesizing 5-6 Minute Master Radio Show Episode")
    print("Show: 'Dil Ki Baatein' with Sanket & Ishita")
    print("Topic: Toxic Work Hours, 4-Day Weeks & Corporate Reform")
    print("==========================================================")

    target_sr = 24000
    combined_audio = []
    # 440ms relaxed broadcast pause between turns
    pause_samples = int(target_sr * 0.44)
    b_hp, a_hp = signal.butter(2, 75 / (target_sr / 2), btype='high')

    total_turns = len(FULL_RADIO_EPISODE)
    total_chars = sum(len(t["text"]) for t in FULL_RADIO_EPISODE)
    print(f"Total script characters: {total_chars} chars across {total_turns} turns.")
    print(f"Estimated credits: ~{total_chars * 0.002:.2f} credits (around ₹8.50)\n")

    for idx, turn_data in enumerate(FULL_RADIO_EPISODE):
        turn_num = turn_data["turn"]
        samples = synthesize_turn_cached(turn_data, target_sr)

        samples -= np.mean(samples)
        samples = signal.filtfilt(b_hp, a_hp, samples)

        # 20ms Smooth Cosine Fade Envelope
        fade_len = int(target_sr * 0.02)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        combined_audio.append(samples)
        if idx < total_turns - 1:
            combined_audio.append(np.zeros(pause_samples, dtype=np.float32))

    full_mix = np.concatenate(combined_audio)

    # Master broadcast peak normalization (-1.0 dBFS)
    max_peak = np.max(np.abs(full_mix))
    if max_peak > 0:
        full_mix = full_mix * (0.891 / max_peak)

    out_file = AUDIO_DIR / "master_podcast_dil_ki_baatein_hustle_culture_5min.mp3"
    sf.write(str(out_file), full_mix, target_sr)

    total_duration = len(full_mix) / target_sr
    minutes = int(total_duration // 60)
    seconds = int(total_duration % 60)

    print("\n==========================================================")
    print(f" [SUCCESS] 5-6 Minute Master Episode Created!")
    print(f" Output File: {out_file}")
    print(f" Total Duration: {total_duration:.2f} seconds ({minutes}m {seconds}s)")
    print(f" Credits Consumed: ~{total_chars * 0.002:.2f} credits")
    print("==========================================================")
    return out_file, total_duration

if __name__ == "__main__":
    build_full_5min_radio_episode()
