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
CACHE_DIR = AUDIO_DIR / "mini_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

MINI_SCRIPT = [
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "Happy weekend, everyone! Welcome to the Future Human Daily Weekend Recap... "
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "[chuckles] That is right! No heavy equations today, folks. Just pure weekend vibes... "
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[playfully] Speaking of wild, Rami... did you catch that video of the new humanoid robot trying to fold laundry?... "
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "Oh, I replayed it three times! It took five minutes to fold one t-shirt, and then accidentally threw the matching sock across the room!... "
    }
]

def find_nearest_zero_crossing(samples, target_idx):
    if target_idx <= 0 or target_idx >= len(samples) - 1:
        return target_idx
    search_win = 120 # 5ms
    start = max(0, target_idx - search_win)
    end = min(len(samples) - 1, target_idx + search_win)
    chunk = samples[start:end]
    zero_crossings = np.where(np.diff(np.signbit(chunk)))[0]
    if len(zero_crossings) > 0:
        best_offset = zero_crossings[np.argmin(np.abs(zero_crossings - (target_idx - start)))]
        return start + best_offset
    return target_idx

def clean_turn_zero_crossing(samples, sample_rate=24000):
    if len(samples) < 2400: return samples

    # 80Hz High Pass Butterworth
    b, a = signal.butter(2, 80 / (sample_rate / 2), btype='high')
    samples = signal.filtfilt(b, a, samples)

    win_len = int(sample_rate * 0.01) # 10ms
    num_wins = len(samples) // win_len
    rms_arr = np.array([np.sqrt(np.mean(samples[i*win_len : (i+1)*win_len]**2)) for i in range(num_wins)])

    speech_wins = np.where(rms_arr > 0.008)[0]
    if len(speech_wins) == 0: return samples

    first_speech_idx = max(0, (speech_wins[0] - 2) * win_len)
    quiet_wins = np.where(rms_arr < 0.002)[0]
    tail_quiet = quiet_wins[quiet_wins > speech_wins[-1]]
    
    if len(tail_quiet) > 0:
        raw_cut_idx = tail_quiet[0] * win_len + int(sample_rate * 0.08)
    else:
        raw_cut_idx = (speech_wins[-1] + 5) * win_len

    raw_cut_idx = min(len(samples), raw_cut_idx)

    start_zc = find_nearest_zero_crossing(samples, first_speech_idx)
    end_zc = find_nearest_zero_crossing(samples, raw_cut_idx)

    trimmed = samples[start_zc:end_zc]

    fade_len = int(sample_rate * 0.03) # 30ms Cosine S-curve
    if len(trimmed) > 2 * fade_len:
        fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
        fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
        trimmed[:fade_len] *= fade_in
        trimmed[-fade_len:] *= fade_out

    return trimmed

def build_mini_sample():
    print("==========================================================", flush=True)
    print("Generating 4-Turn Mini Sample (Zero-Crossing + Ellipsis)", flush=True)
    print("==========================================================", flush=True)

    sample_rate = 24000
    combined_audio = []
    silence_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    for idx, turn in enumerate(MINI_SCRIPT):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        cache_file = CACHE_DIR / f"turn_{idx+1}_{speaker}.npy"

        raw_samples = None
        if cache_file.exists():
            print(f" -> Turn {idx+1}/4 [{speaker}] loaded from CACHE", flush=True)
            raw_samples = np.load(str(cache_file))
        else:
            success = False
            for attempt in range(5):
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
                            raw_samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                            np.save(str(cache_file), raw_samples)
                            print(f" -> Turn {idx+1}/4 [{speaker}] synthesized via {model_name}", flush=True)
                            success = True
                            break
                    except Exception as e:
                        print(f"    Attempt {attempt+1}: Quota delay ({e}), waiting 12s...", flush=True)
                        time.sleep(12)
                if success: break

        if raw_samples is not None:
            cleaned = clean_turn_zero_crossing(raw_samples, sample_rate)
            combined_audio.append(cleaned)
            combined_audio.append(silence_gap)
            time.sleep(4)

    full_track = np.concatenate(combined_audio)
    max_p = np.max(np.abs(full_track))
    if max_p > 0: full_track = full_track * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_22_mini_4turn_zero_noise.mp3"
    out_wav = AUDIO_DIR / "sample_22_mini_4turn_zero_noise.wav"

    sf.write(str(out_wav), full_track, sample_rate)
    sf.write(str(out_mp3), full_track, sample_rate)

    duration = len(full_track) / sample_rate
    print("==========================================================", flush=True)
    print(f"[COMPLETE] Saved Mini Sample 22: {out_mp3}", flush=True)
    print(f"Duration: {duration:.2f}s ({len(MINI_SCRIPT)} turns, 3 transitions)", flush=True)
    print("==========================================================", flush=True)

if __name__ == "__main__":
    build_mini_sample()
