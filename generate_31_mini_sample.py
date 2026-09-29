import os
import time
import base64
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = AUDIO_DIR / "mini_cache_31"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

MINI_SCRIPT_31 = [
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[upbeat] Happy weekend, everyone! Welcome to the Future Human Daily Weekend Recap. Alex and Elena are off taking a well-deserved break today and will be back bright and early Monday morning—so I am Veda with Rami, and we are kicking back with your Saturday morning coffee."
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "[chuckles] [warmly] That is right! No heavy quantum physics equations today, folks. Just pure weekend vibes and the funniest, wildest tech stories that broke this week."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[playfully] Speaking of wild, Rami... did you catch that video of the new humanoid robot trying to fold laundry?"
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "[warmly] Oh, I replayed it three times! It took five minutes to fold one t-shirt, and then accidentally threw the matching sock across the living room! [chuckles] Honestly, that is still better than my college roommate used to do."
    }
]

def build_31_mini_sample():
    print("==========================================================", flush=True)
    print("Generating 4-Turn Gemini 3.1 Mini Sample (Veda & Rami)", flush=True)
    print("==========================================================", flush=True)

    sample_rate = 24000
    combined_audio = []
    silence_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    b_hp, a_hp = signal.butter(2, 80 / (sample_rate / 2), btype='high')

    for idx, turn in enumerate(MINI_SCRIPT_31):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        cache_file = CACHE_DIR / f"turn_31_{idx+1}_{speaker}.npy"

        raw_samples = None
        if cache_file.exists():
            print(f" -> Turn {idx+1}/4 [{speaker}] loaded from CACHE", flush=True)
            raw_samples = np.load(str(cache_file))
        else:
            success = False
            for attempt in range(8):
                try:
                    resp = client.models.generate_content(
                        model='gemini-3.1-flash-tts-preview',
                        contents=text,
                        config=types.GenerateContentConfig(
                            response_modalities=["AUDIO"],
                            speech_config=types.SpeechConfig(
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                                )
                            )
                        )
                    )
                    part = resp.candidates[0].content.parts[0]
                    if part.inline_data:
                        data = part.inline_data.data
                        if isinstance(data, str): data = base64.b64decode(data)
                        raw_samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                        np.save(str(cache_file), raw_samples)
                        print(f" -> Turn {idx+1}/4 [{speaker}] synthesized via gemini-3.1-flash-tts-preview!", flush=True)
                        success = True
                        break
                except Exception as e:
                    print(f"    Attempt {attempt+1}: Quota delay ({e}), retrying in 12s...", flush=True)
                    time.sleep(12)
                if success: break

        if raw_samples is not None:
            # High Pass 80Hz
            turn_audio = signal.filtfilt(b_hp, a_hp, raw_samples)
            
            # Apply 20ms Cosine S-curve boundary fade
            fade_len = int(sample_rate * 0.02)
            if len(turn_audio) > 2 * fade_len:
                fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
                fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
                turn_audio[:fade_len] *= fade_in
                turn_audio[-fade_len:] *= fade_out

            combined_audio.append(turn_audio)
            combined_audio.append(silence_gap)
            time.sleep(3)

    if not combined_audio:
        print("[Error] No audio chunks generated.", flush=True)
        return

    full_track = np.concatenate(combined_audio)
    max_p = np.max(np.abs(full_track))
    if max_p > 0: full_track = full_track * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_27_mini_31_veda_rami.mp3"
    out_wav = AUDIO_DIR / "sample_27_mini_31_veda_rami.wav"

    sf.write(str(out_wav), full_track, sample_rate)
    sf.write(str(out_mp3), full_track, sample_rate)

    duration = len(full_track) / sample_rate
    print("==========================================================", flush=True)
    print(f"[COMPLETE] Saved Gemini 3.1 Mini Sample 27: {out_mp3}", flush=True)
    print(f"Duration: {duration:.2f}s (4 turns, 3 transitions)", flush=True)
    print("==========================================================", flush=True)

if __name__ == "__main__":
    build_31_mini_sample()
