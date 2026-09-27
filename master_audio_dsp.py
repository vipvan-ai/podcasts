import os
import sys
import glob
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"

def master_episode(ep_num="003", sample_rate=24000):
    cache_dir = AUDIO_DIR / f"cache_ep{ep_num}"
    if not cache_dir.exists():
        print(f"[Error] Cache directory {cache_dir} does not exist!")
        return False

    pcm_files = sorted(cache_dir.glob("turn_*.pcm"), key=lambda p: p.name)
    if not pcm_files:
        print(f"[Error] No turn PCM files found in {cache_dir}")
        return False

    print(f"==========================================================")
    print(f"[DSP MASTERING PASS] Episode {ep_num} ({len(pcm_files)} turns)")
    print(f"==========================================================")

    b, a = signal.butter(2, 80 / (sample_rate / 2), btype='high')
    combined_samples = []
    pause_samples = int(sample_rate * 0.35)  # 350ms natural pause between turns

    for pcm_path in pcm_files:
        raw_bytes = pcm_path.read_bytes()
        if not raw_bytes:
            continue
        
        # 16-bit PCM signed LE -> float32 [-1.0, 1.0]
        samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # DC offset removal
        samples -= np.mean(samples)

        # 80Hz Butterworth High-Pass Filter
        if len(samples) > 100:
            samples = signal.filtfilt(b, a, samples)

        # 20ms Cosine S-curve boundary fade
        fade_len = int(sample_rate * 0.02)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        combined_samples.append(samples)
        combined_samples.append(np.zeros(pause_samples, dtype=np.float32))

    full_audio = np.concatenate(combined_samples)

    # Peak normalization to -1.0 dBFS (0.891)
    max_peak = np.max(np.abs(full_audio))
    if max_peak > 0:
        target_peak = 10 ** (-1.0 / 20.0) # ~0.89125
        full_audio = full_audio * (target_peak / max_peak)

    out_mp3 = AUDIO_DIR / f"ep-{ep_num}.mp3"
    out_wav = AUDIO_DIR / f"ep-{ep_num}-master.wav"

    print(f" -> Saving Master WAV to {out_wav}...")
    sf.write(str(out_wav), full_audio, sample_rate)

    print(f" -> Saving Master MP3 to {out_mp3}...")
    sf.write(str(out_mp3), full_audio, sample_rate)

    duration_sec = len(full_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    print(f"==========================================================")
    print(f"[MASTERING COMPLETE] EP {ep_num} Duration: {minutes}m {seconds}s ({duration_sec:.2f}s)")
    print(f"Output MP3: {out_mp3}")
    print(f"==========================================================")
    return True

if __name__ == "__main__":
    ep = sys.argv[1] if len(sys.argv) > 1 else "003"
    master_episode(ep)
