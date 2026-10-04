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
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = AUDIO_DIR / "trailer_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load .env
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

TTS_MODELS = [
    'gemini-3.8-flash-tts',
    'gemini-3.8-flash-lite-tts',
    'gemini-2.5-flash-preview-tts',
    'gemini-3.1-flash-tts-preview'
]

# Official Launch Trailer Script: Coming October 5th
TRAILER_SCRIPT = [
    {
        "speaker": "Maya",
        "voice": "Kore",
        "text": "[warmly] [playfully] Have you ever received a Venmo request from a friend for two dollars and forty-seven cents... and wondered if modern society is completely broken?"
    },
    {
        "speaker": "Julian",
        "voice": "Puck",
        "text": "[chuckles] Or sat trapped in a twelve-person group chat wishing there was an eject button that didn't start an entire family war?"
    },
    {
        "speaker": "Maya",
        "voice": "Kore",
        "text": "[laughs] Welcome to The Unwritten Code—the survival guide to modern human behavior, etiquette, and life's weirdest everyday dilemmas."
    },
    {
        "speaker": "Julian",
        "voice": "Puck",
        "text": "[warmly] I am Julian Cross..."
    },
    {
        "speaker": "Maya",
        "voice": "Kore",
        "text": "...and I am Maya Lin. Every weekday morning, we unpack the unspoken rules nobody taught you in school—from office Slack anxiety and first-date politics, to who actually owns the middle seat armrests on an airplane."
    },
    {
        "speaker": "Julian",
        "voice": "Puck",
        "text": "[chuckles] Plus, every Saturday on The Weekend Docket, we put your wildest real-life dilemmas on trial and hand down the definitive verdict."
    },
    {
        "speaker": "Maya",
        "voice": "Kore",
        "text": "[excitedly] Our daily drops start this Monday, October 5th! Hit the follow button right now on Spotify and Apple Podcasts so you never miss an episode."
    },
    {
        "speaker": "Julian",
        "voice": "Puck",
        "text": "[warmly] See you Monday morning. Don't break the code!"
    }
]

def synthesize_turn(turn_idx, voice_name, text):
    cache_path = CACHE_DIR / f"turn_{turn_idx}_{voice_name}.npy"
    if cache_path.exists():
        print(f" -> Turn {turn_idx} loaded from cache!")
        return np.load(str(cache_path))

    for model_name in TTS_MODELS:
        for attempt in range(2):
            try:
                print(f"Synthesizing Turn {turn_idx} [{voice_name}] with {model_name}...")
                resp = client.models.generate_content(
                    model=model_name,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                            )
                        )
                    )
                )
                part = resp.candidates[0].content.parts[0]
                if part.inline_data:
                    data = part.inline_data.data
                    if isinstance(data, str):
                        data = base64.b64decode(data)
                    raw_samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    np.save(str(cache_path), raw_samples)
                    print(f" -> Turn {turn_idx} generated successfully and cached!")
                    return raw_samples
            except Exception as e:
                err_str = str(e)
                print(f"   [{model_name}] attempt {attempt+1} error: {err_str[:120]}...")
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print("   Rate limit encountered. Waiting 16s before next attempt...")
                    time.sleep(16)
                else:
                    time.sleep(2)
    return None

def apply_broadcast_master(audio_samples, sample_rate=24000):
    if len(audio_samples) < 500:
        return audio_samples

    # 1. 80Hz High Pass to eliminate DC offset / sub-bass rumble
    b_hp, a_hp = signal.butter(2, 80 / (sample_rate / 2), btype='high')
    audio_samples = signal.filtfilt(b_hp, a_hp, audio_samples)

    # 2. 7.2kHz gentle Low Pass filter to eliminate harsh digital sibilance
    b_lp, a_lp = signal.butter(3, 7200.0 / (sample_rate / 2), btype='low')
    audio_samples = signal.filtfilt(b_lp, a_lp, audio_samples)

    # 3. Warm 150Hz Peak Filter (+3.5 dB)
    f0 = 150.0
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

    b_eq = np.array([b0, b1, b2]) / a0
    a_eq = np.array([a0, a1, a2]) / a0
    audio_samples = signal.filtfilt(b_eq, a_eq, audio_samples)
    return audio_samples

def generate_official_trailer():
    print("==========================================================")
    print("Building Official Launch Trailer: The Unwritten Code")
    print("Release Target: Monday, October 5th, 2026")
    print("==========================================================")
    sample_rate = 24000
    cleaned_turns = []
    
    # 0.28s comfortable conversational transition gap between hosts
    silence_gap = np.zeros(int(sample_rate * 0.28), dtype=np.float32)

    for idx, turn in enumerate(TRAILER_SCRIPT):
        turn_idx = idx + 1
        samples = synthesize_turn(turn_idx, turn["voice"], turn["text"])
        if samples is None:
            print(f"Failed to generate turn {turn_idx}!")
            return
        
        # Apply broadcast warmth
        warm = apply_broadcast_master(samples, sample_rate)

        # 25ms Cosine S-curve boundary fade
        fade_len = int(sample_rate * 0.025)
        if len(warm) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            warm[:fade_len] *= fade_in
            warm[-fade_len:] *= fade_out

        cleaned_turns.append(warm)
        if idx < len(TRAILER_SCRIPT) - 1:
            cleaned_turns.append(silence_gap)
        
        # Polite delay to respect API rate limits
        time.sleep(3)

    full_track = np.concatenate(cleaned_turns)
    
    # Peak normalization to -1.0 dBFS (0.891)
    max_p = np.max(np.abs(full_track))
    if max_p > 0:
        full_track = full_track * (0.891 / max_p)

    out_wav = AUDIO_DIR / "unwritten_code_trailer.wav"
    out_mp3 = AUDIO_DIR / "unwritten_code_trailer.mp3"

    sf.write(str(out_wav), full_track, sample_rate)
    sf.write(str(out_mp3), full_track, sample_rate)

    duration = len(full_track) / sample_rate
    print("\n==========================================================")
    print(f"[SUCCESS] Official Trailer saved to: {out_mp3}")
    print(f"Total Duration: {duration:.2f} seconds (~{int(duration // 60)}m {int(duration % 60)}s)")
    print("==========================================================")

if __name__ == "__main__":
    generate_official_trailer()
