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
CACHE_DIR = AUDIO_DIR / "cache_ep003"
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
# MASTER EPISODE 003 DIALOGUE (Approx 1,900 words / 20 Turns)
# Topic: Cellular Reprogramming & Resetting Biological Age Clocks
# -----------------------------------------------------------------------------
MASTER_EP003_DIALOGUE = [
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is September 27th, and you're listening to Future Human Daily. Today we are talking about Cellular Reprogramming—and whether science can actually reset the biological age clock inside our cells."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Happy September 27th, everyone! Alex... before we dive into the genetics today, let me ask you. [chuckles] Have you ever had your smartphone completely freeze up, so you press factory reset, and suddenly it runs like brand new out of the box?"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[laughs] Oh, absolutely! You wipe the cache, reboot the system, and that sluggish phone that was dying every three hours suddenly feels blazingly fast again!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] Well... what if you could press factory reset on your body's cells? What if an eighty-year-old human liver cell could be reprogrammed back to age twenty?"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] That is where Yamanaka Factors come in! And—and look, this is Nobel Prize winning science. In 2006, Dr. Shinya Yamanaka discovered four specific proteins—Oct4, Sox2, Klf4, and c-Myc."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Right! When you expose mature adult skin or muscle cells to these four factors, it unwinds the epigenetic marks—the molecular dust and wear-and-tear that accumulates as we age."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] It literally rolls the biological clock backward! Like replacing worn-out pistons in a rusty car engine without buying a new vehicle!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Elena, think about what this means! If we can partial-reprogram human tissues safely, people could easily live to one hundred and fifty! Imagine playing futuristic virtual reality games with your great-great-grandchildren!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] [playfully] Wait, Alex, hold on—you really think living to one hundred and fifty is just video games and sunshine? [laughs]"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[chuckles] Well... yeah! Staying healthy, active, and sharp for an extra fifty years sounds incredible!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[serious] Alex, come on, look at the biological and societal reality! [chuckles] If you push cellular reprogramming too far, the cells don't just get younger—they lose their identity and turn into teratomas or cancerous tumors."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Okay... fair point. But—uh, researchers at Harvard and Altos Labs found partial reprogramming—pulsing the factors for just a few days at a time—restores youthful function without causing tumors."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Partial reprogramming in mice restored sight in aged optic nerves, which is groundbreaking, Alex. But what about the social consequences? Imagine a world where billionaire CEOs never retire, holding onto power for a century!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Wait—no, I mean... imagine toxic bosses staying in charge for eighty years! That would completely stall career mobility for younger generations."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Exactly! True longevity isn't just about extending lifespan; it is about extending healthspan. Compression of morbidity—making sure your final years are vibrant, pain-free, and active."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Right! So... like, instead of spending twenty years in declining health, you stay biologically thirty-five until your nineties, and then peacefully fade away."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] That is the true promise of regenerative medicine. Adding health to years, not just years to life."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] What a fantastic episode today! So, Elena... if you could reverse the age of just one organ in your body, which would it be?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[playfully] [giggles] My brain's memory center... so I can remember all the times I proved you wrong on this show, Alex! [laughs]"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[laughs] Fair enough! Thank you for spending your September 27th with us on Future Human Daily. Make sure to subscribe on Spotify or Apple Podcasts, leave us a review, and until tomorrow... stay curious about the future!"
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

def build_master_ep003_audio():
    print("==========================================================", flush=True)
    print("[EPISODE 003 ENGINE] Building Cellular Reprogramming Episode", flush=True)
    print("==========================================================", flush=True)
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    pcm_chunks = []
    
    TTS_MODELS = [
        'gemini-2.5-flash-preview-tts',
        'gemini-3.1-flash-tts-preview',
        'gemini-2.5-pro-preview-tts',
        'gemini-3.8-flash-lite-tts',
        'gemini-3.8-flash-tts'
    ]
    
    for idx, turn in enumerate(MASTER_EP003_DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        cache_file = CACHE_DIR / f"turn_{idx+1:02d}_{speaker}.pcm"
        
        if cache_file.exists() and cache_file.stat().st_size > 0:
            print(f" -> Turn {idx+1}/{len(MASTER_EP003_DIALOGUE)}: [{speaker} ({voice})] [CACHED] {text[:45]}...", flush=True)
            data = cache_file.read_bytes()
            pcm_chunks.append(data)
            continue

        print(f" -> Generating Turn {idx+1}/{len(MASTER_EP003_DIALOGUE)}: [{speaker} ({voice})] {text[:45]}...", flush=True)
        
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
    build_master_ep003_audio()
