import os
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def master_veda_rami_clean():
    # Load all 5 turns synthesized for sample 9 or synthesize clean PCM
    sample_rate = 24000
    b_hp, a_hp = signal.butter(2, 80 / (sample_rate / 2), btype='high')
    
    # We load the turn chunks, apply trailing spike trim + 20ms cosine fade
    # Let's re-read the turns if saved or apply DSP filter to current audio
    in_file = AUDIO_DIR / "sample_09_veda_rami_bioscience_ai.mp3"
    if not in_file.exists():
        print("Input sample 9 not found!")
        return

    data, sr = sf.read(str(in_file))
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    # 1. High pass filter 80Hz
    clean_audio = signal.filtfilt(b_hp, a_hp, data)

    # 2. Soft noise gate for inter-turn quiet spaces
    # Calculate energy envelope over 10ms windows
    window = int(sr * 0.01) # 10ms
    energy = np.zeros_like(clean_audio)
    for i in range(0, len(clean_audio) - window, window):
        chunk_e = np.sqrt(np.mean(clean_audio[i:i+window]**2))
        energy[i:i+window] = chunk_e

    # Threshold for silence gap (-42 dB)
    silence_thresh = 10 ** (-42.0 / 20.0)
    quiet_mask = energy < silence_thresh
    clean_audio[quiet_mask] *= 0.05 # Mute transition noise completely

    # Peak normalize
    max_peak = np.max(np.abs(clean_audio))
    if max_peak > 0:
        clean_audio = clean_audio * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_09_veda_rami_bioscience_ai_clean_mastered.mp3"
    sf.write(str(out_file), clean_audio, sr)
    print(f"[MASTERED] Cleaned DSP Veda & Rami sample saved to: {out_file}")

if __name__ == "__main__":
    master_veda_rami_clean()
