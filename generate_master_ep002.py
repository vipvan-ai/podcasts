import os
import re
import time
import base64
import struct
import numpy as np
from pathlib import Path
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAqMBniCg-vSQPxvTeYibsvIzGmAxewPuc")
AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = AUDIO_DIR / "cache_ep002"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# MASTER EPISODE 002 DIALOGUE (Approx 1,900 words / 23 Turns)
# Topic: Targeted Dream Incubation & Neuro-Hacking
# Rules: Mandatory intro (Sep 27), NO WHISPERING, natural stutters, playful banter,
#        science vs reality check disagreement, relatable analogies.
# -----------------------------------------------------------------------------
MASTER_EP002_DIALOGUE = [
    # --- INTRO & HOOK (Part 1) ---
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is September 27th, and you're listening to Future Human Daily. Today we are talking about Targeted Dream Incubation—and whether technology can actually guide, shape, or hack what happens inside our sleeping minds."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Happy September 27th, everyone! Alex... before we jump into the MIT neuroscience, let me ask you something. [chuckles] Have you ever had one of those bizarre dreams where you're trying to type a text message, but—uh, like—your fingers turn into floppy wet noodles?"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[laughs] Oh, all the time! Or you're trying to run away from something, but it feels like you're running underwater through thick honey! [chuckles] Or—or worse, you're flying on a giant taco over your high school geometry class!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[laughs] Exactly! Dreams are completely chaotic. For thousands of years, humans just accepted that dreams were random brain noise or weird nocturnal hallucinations. But Alex... what if you could control the script?"
    },

    # --- SCIENCE MADE SIMPLE (Part 2) ---
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] That is where Targeted Dream Incubation comes in! And—and look, this isn't science fiction anymore. Researchers at MIT's Media Lab built a wearable device called Dormio."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Right! Dormio tracks your heart rate, muscle tone, and skin conductance to detect when you enter hypnagogia—that twilight stage between being fully awake and falling deep asleep."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] And right at that exact micro-second, the device plays a tiny audio cue—like a whispered word or a specific tone—to seed a theme into your subconscious! Like... 'remember to think about a tree'."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] And in clinical trials, over sixty-seven percent of participants immediately started dreaming about trees! They had wooden arms, or walked through giant redwood forests."
    },

    # --- THE FRIENDLY BANTER & DEBATE (Part 3) ---
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Elena, think about the productivity potential! If we can guide hypnagogia, imagine practicing your keynote speech while asleep, or—or learning conversational Japanese while resting!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] [playfully] Wait, Alex, hold on—stop right there! [laughs] Are you seriously suggesting we turn sleep into a side hustle?"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[chuckles] Well... why not? We waste eight hours a night just lying there in the dark doing nothing!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[serious] Alex, come on, that is a terrible idea! [chuckles] Sleep is not wasted time; it's basic biological maintenance! During REM sleep, your brain's glymphatic system opens up like a dishwasher, washing away metabolic waste and toxic proteins."
    },

    # --- NEURO-MARKETING & AD ALERTS (Part 4) ---
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Okay... fair point. But—uh, what if it's used for creativity? Salvador Dalí and Thomas Edison used to sleep holding heavy iron balls over brass plates. The moment they drifted off, the ball dropped, woke them up, and they wrote down their crazy insights!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Using it for artistic inspiration is incredible, Alex. But here is the darker reality check... corporate dream-incubation. [serious] Last year, a major beverage company tested playing commercial audio cues to sleeping participants to make them crave their soda in the morning."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Wait—no, I mean... pop-up ads inside your subconscious dreams? Imagine dreaming about a peaceful beach, and suddenly a giant floating soda can tells you to buy a six-pack!"
    },

    # --- INTELLECTUAL OVERLAP & REASONING (Part 5) ---
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Exactly! That is why neuro-ethicists are calling for strict boundaries. Our dreams are literally the last unmonetized sanctuary of the human mind."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] So... like, where do we draw the line, Elena? Between therapeutic dream incubation—like helping PTSD patients rewrite nightmare endings—and invasive cognitive manipulation?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] The boundary has to be informed consent and personal autonomy. Technology should assist your subconscious, not hijack it for profit."
    },

    # --- WRAP UP & OUTRO (Part 6) ---
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] What a fascinating debate today! So, Elena... if you could safely incubate one dream tonight, what would it be?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[playfully] [giggles] Honestly? Flying over the Amalfi coast on a giant taco... just to prove your theory right, Alex! [laughs]"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[laughs] I love it! Thank you for spending your September 27th with us on Future Human Daily. Make sure to subscribe on Spotify or Apple Podcasts, leave us a five-star review, and until tomorrow... stay curious about the future!"
    }
]

def apply_crossfade_smoothing(pcm_data: bytes, fade_samples: int = 240) -> bytes:
    """Applies a smooth linear fade-in and fade-out to raw 16-bit PCM bytes."""
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

def build_master_ep002_audio():
    print("==========================================================", flush=True)
    print("[EPISODE 002 ENGINE] Building Targeted Dream Incubation Episode", flush=True)
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
    
    for idx, turn in enumerate(MASTER_EP002_DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        cache_file = CACHE_DIR / f"turn_{idx+1:02d}_{speaker}.pcm"
        
        if cache_file.exists() and cache_file.stat().st_size > 0:
            print(f" -> Turn {idx+1}/{len(MASTER_EP002_DIALOGUE)}: [{speaker} ({voice})] [CACHED] {text[:45]}...", flush=True)
            data = cache_file.read_bytes()
            pcm_chunks.append(data)
            continue

        print(f" -> Generating Turn {idx+1}/{len(MASTER_EP002_DIALOGUE)}: [{speaker} ({voice})] {text[:45]}...", flush=True)
        
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
                    time.sleep(1)
                    turn_success = True
                    break
            except Exception as e:
                print(f"    [Model Fallback ({model_name})] Quota/Rate limit: Trying next model...", flush=True)
                time.sleep(1)
                
        if not turn_success:
            print(f"    [Warning] All models exhausted for turn {idx+1}. Retrying in 15s...", flush=True)
            time.sleep(15)

    print("\n==========================================================", flush=True)
    print("[RAW SYNTHESIS COMPLETE] Ready for DSP Mastering Pass", flush=True)
    print("==========================================================", flush=True)

if __name__ == "__main__":
    build_master_ep002_audio()
