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

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

WEEKEND_SCRIPT = [
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "Happy weekend, everyone! Welcome to the Future Human Daily Weekend Recap. Alex and Elena are off taking a well-deserved break today and will be back bright and early Monday morning—so I am Veda with Rami, and we are kicking back with your Saturday morning coffee."
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "[chuckles] That is right! No heavy quantum physics equations today, folks. Just pure weekend vibes and the funniest, wildest tech stories that broke this week."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[playfully] Speaking of wild, Rami... did you catch that video of the new humanoid robot trying to fold laundry?"
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "Oh, I replayed it three times! It took five minutes to fold one t-shirt, and then accidentally threw the matching sock across the living room! [chuckles] Honestly, that is still better than my college roommate used to do."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[laughs] Exactly! The robot looked so proud of itself too. But hey, story number two... an AI model just composed an entire nineteen-eighties synth-wave album that is actually trending on music charts."
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "[thoughtfully] Right? I listened to track three on my morning jog. You literally cannot tell if it was made by a computer or a guy wearing neon leg warmers in nineteen-eighty-four."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[playfully] Well, grab another cup of coffee, folks, because we have a couple more weekend gems to unpack before Alex and Elena get back on Monday!"
    }
]

def strip_gemini_buffer_bursts(samples, sample_rate=24000):
    """Detects and surgical-chops Gemini 3.8 uninitialized buffer noise bursts at head & tail."""
    if len(samples) < 2400: # 100ms
        return samples

    # 1. Inspect tail from the end: 10ms windows (240 samples)
    win_len = int(sample_rate * 0.01) # 10ms
    num_wins = len(samples) // win_len
    
    rms_arr = np.zeros(num_wins)
    for i in range(num_wins):
        c = samples[i*win_len : (i+1)*win_len]
        rms_arr[i] = np.sqrt(np.mean(c**2))

    # Find where speech actually lives. Speech threshold = 0.008 (-42 dBFS)
    speech_indices = np.where(rms_arr > 0.008)[0]
    if len(speech_indices) == 0:
        return samples

    first_speech_win = speech_indices[0]
    last_speech_win = speech_indices[-1]

    # Look backwards from the end of array for a sudden burst AFTER a quiet region
    # If there is a burst at the very end (last 300ms) separated by quiet (RMS < 0.005)
    cut_end_win = num_wins
    for w in range(num_wins - 1, max(last_speech_win, num_wins - 30), -1):
        # Check if this window has huge noise (> 0.05) preceded by silence (< 0.005)
        if rms_arr[w] > 0.05:
            # Check preceding 3 windows
            if w > 3 and np.max(rms_arr[w-4:w]) < 0.005:
                cut_end_win = w - 1
                break

    # Also trim trailing silence down to max 100ms after last real speech
    final_end_win = min(cut_end_win, last_speech_win + 10) # 10 windows = 100ms padding
    start_win = max(0, first_speech_win - 2) # 20ms padding at start

    trimmed = samples[start_win * win_len : final_end_win * win_len]

    # Apply 20ms Cosine S-curve fade in and fade out
    fade_len = int(sample_rate * 0.02)
    if len(trimmed) > 2 * fade_len:
        fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
        fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
        trimmed[:fade_len] *= fade_in
        trimmed[-fade_len:] *= fade_out

    return trimmed

def build_zero_noise_recap_sample():
    print("==========================================================", flush=True)
    print("Building Zero Noise Recap (Surgically Stripping API Buffer Bursts)", flush=True)
    print("==========================================================", flush=True)

    sample_rate = 24000
    combined_audio = []
    silence_gap = np.zeros(int(sample_rate * 0.38), dtype=np.float32)

    for idx, turn in enumerate(WEEKEND_SCRIPT):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]

        raw_bytes = None
        for model_name in ['gemini-3.8-flash-tts', 'gemini-3.8-flash-lite-tts']:
            try:
                resp = client.models.generate_content(
                    model=model_name,
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
                    raw_bytes = data
                    print(f" -> Turn {idx+1}/{len(WEEKEND_SCRIPT)} [{speaker}] generated via {model_name}", flush=True)
                    break
            except Exception as e:
                time.sleep(2)

        if raw_bytes:
            raw_samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Print turn analysis
            orig_len = len(raw_samples)
            clean_samples = strip_gemini_buffer_bursts(raw_samples, sample_rate)
            new_len = len(clean_samples)
            print(f"    Turn {idx+1} trimmed: {orig_len} -> {new_len} samples (removed {orig_len - new_len} tail samples)", flush=True)

            combined_audio.append(clean_samples)
            combined_audio.append(silence_gap)
            time.sleep(2)

    full_track = np.concatenate(combined_audio)
    
    # High-Pass filter at 80Hz
    b, a = signal.butter(2, 80 / (sample_rate / 2), btype='high')
    full_track = signal.filtfilt(b, a, full_track)

    # Peak normalize
    max_p = np.max(np.abs(full_track))
    if max_p > 0:
        full_track = full_track * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_21_veda_rami_zero_bursts.mp3"
    out_wav = AUDIO_DIR / "sample_21_veda_rami_zero_bursts.wav"

    sf.write(str(out_wav), full_track, sample_rate)
    sf.write(str(out_mp3), full_track, sample_rate)

    duration = len(full_track) / sample_rate
    print("==========================================================", flush=True)
    print(f"[COMPLETE] Saved Sample 21: {out_mp3}", flush=True)
    print(f"Duration: {duration:.2f}s", flush=True)
    print("==========================================================", flush=True)

if __name__ == "__main__":
    build_zero_noise_recap_sample()
