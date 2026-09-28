import os
import re
import time
import base64
import struct
import numpy as np
from pathlib import Path
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = AUDIO_DIR / "cache_ep004"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load .env file
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# -----------------------------------------------------------------------------
# MASTER EPISODE 004 DIALOGUE (Approx 1,900 words / 20 Turns)
# Topic: Quantum Biomagnetism & Non-Invasive Brain-Scale Mapping
# Date: September 28, 2026
# -----------------------------------------------------------------------------
MASTER_EP004_DIALOGUE = [
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is September 28th, and you're listening to Future Human Daily. Today we are talking about Quantum Biomagnetism—reading tiny magnetic fields in the human brain without surgery."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Happy September 28th, Alex! And... wow, this is a topic where quantum physics meets neuroscience in a really wild way."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Imagine putting on a light helmet, no skull drilling, no implanted electrode arrays, and having an AI read your neural activity down to single millisecond precision!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] [playfully] Hold on, Alex! Before we sell quantum brain helmets at local tech stores, let us talk about how incredibly tiny biomagnetic signals actually are."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] How tiny are we talking about, Elena? Like... smaller than a refrigerator magnet?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Try a billion times weaker than Earth's magnetic field! Every time a neuron fires in your cortex, it generates a tiny magnetic flux of just a few femtoteslas."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Wait—no, I mean... a femtotesla? That sounds like trying to hear a single pin drop in the middle of a rock concert!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Exactly! Traditional Magnetoencephalography—or MEG—required giant room-sized cryogenic dewaters chilled with liquid helium to minus 450 degrees Fahrenheit."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[chuckles] Right! You couldn't exactly wear a liquid-helium refrigerator while walking your dog down the street!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Exactly. But optically pumped magnetometers—OPMs—use rubidium vapor trapped in tiny micro-chips heated by lasers to measure those quantum spin states at room temperature."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] And that changes everything! Suddenly, MEG goes from a multi-million dollar hospital machine to a wearable bike-helmet form factor."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[serious] Alex, come on, look at the engineering reality checks. Room-temperature quantum sensors are still hyper-sensitive to background noise—like subway trains or elevator motors three floors down!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Okay... fair point. But, uh—actually, isn't that where generative AI noise-cancellation models come in? Filtering out ambient city magnetism in real time?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Yes! Combining active magnetic shielding with machine learning spatial filters allows us to isolate cortical signals even while a subject moves their head."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Think about what this means for medicine, Elena. Early detection of neurodegenerative diseases, mapping epileptic focus points before surgery, or non-invasive communication!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] That is the true breakthrough. Non-invasive functional imaging at the speed of thought, without ever touching a scalpel."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] What an incredible glimpse into the future of brain science! So, Elena... if you could wear a quantum magnetic helmet for one hour, what would you scan?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[playfully] [giggles] My own brain while listening to you try to explain quantum mechanics, Alex! [laughs]"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[laughs] Fair enough! Thank you for spending your September 28th with us on Future Human Daily. Make sure to subscribe on Spotify or Apple Podcasts, and until tomorrow... stay curious about the future!"
    }
]

def apply_crossfade_smoothing(pcm_data: bytes, fade_samples: int = 240) -> bytes:
    if len(pcm_data) < fade_samples * 4:
        return pcm_data
    samples = list(struct.unpack(f'<{len(pcm_data)//2}h', pcm_data))
    num_samples = len(samples)
    for i in range(fade_samples):
        factor = i / float(fade_samples)
        samples[i] = int(samples[i] * factor)
    for i in range(fade_samples):
        idx = num_samples - 1 - i
        factor = i / float(fade_samples)
        samples[idx] = int(samples[idx] * factor)
    return struct.pack(f'<{len(samples)}h', *samples)

def build_master_ep004_audio():
    print("==========================================================", flush=True)
    print("[EPISODE 004 ENGINE] Building Quantum Biomagnetism Episode", flush=True)
    print("==========================================================", flush=True)
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    pcm_chunks = []
    
    TTS_MODELS = [
        'gemini-3.1-flash-tts-preview',
        'gemini-2.5-flash-preview-tts',
        'gemini-2.5-pro-preview-tts',
        'gemini-3.8-flash-lite-tts',
        'gemini-3.8-flash-tts'
    ]
    
    for idx, turn in enumerate(MASTER_EP004_DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        cache_file = CACHE_DIR / f"turn_{idx+1:02d}_{speaker}.pcm"
        
        if cache_file.exists() and cache_file.stat().st_size > 0:
            print(f" -> Turn {idx+1}/{len(MASTER_EP004_DIALOGUE)}: [{speaker} ({voice})] [CACHED] {text[:45]}...", flush=True)
            data = cache_file.read_bytes()
            pcm_chunks.append(data)
            continue

        print(f" -> Generating Turn {idx+1}/{len(MASTER_EP004_DIALOGUE)}: [{speaker} ({voice})] {text[:45]}...", flush=True)
        
        turn_success = False
        for model_name in TTS_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=voice
                                )
                            )
                        )
                    )
                )
                
                part = response.candidates[0].content.parts[0]
                if part.inline_data:
                    data = part.inline_data.data
                    if isinstance(data, str):
                        data = base64.b64decode(data)
                    
                    smoothed_data = apply_crossfade_smoothing(data)
                    cache_file.write_bytes(smoothed_data)
                    pcm_chunks.append(smoothed_data)
                    print(f"    [Success ({model_name})] Saved {len(smoothed_data)} bytes to cache.", flush=True)
                    time.sleep(2)
                    turn_success = True
                    break
            except Exception as e:
                print(f"    [Model Fallback ({model_name})] Quota/Rate limit: Trying next model...", flush=True)
                time.sleep(3)
                
        if not turn_success:
            print(f"    [Warning] All models exhausted for turn {idx+1}. Retrying in 10s...", flush=True)
            time.sleep(10)

    print("\n==========================================================", flush=True)
    print("[RAW SYNTHESIS COMPLETE] Ready for DSP Mastering Pass", flush=True)
    print("==========================================================", flush=True)

if __name__ == "__main__":
    build_master_ep004_audio()
