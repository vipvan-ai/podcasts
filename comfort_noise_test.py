import os
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def process_comfort_noise():
    in_file = AUDIO_DIR / "sample_11_veda_rami_natural_clean.mp3"
    if not in_file.exists():
        print("Input file not found!")
        return

    data, sr = sf.read(str(in_file))
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    print("==========================================================")
    print("Building Steady Ambient Room Bed (Eliminates Noise Pumping)")
    print("==========================================================")

    # Generate subtle warm pink noise room tone at -55 dBFS
    num_samples = len(data)
    unequal_noise = np.random.randn(num_samples).astype(np.float32)
    # Low pass filter noise at 400Hz to make it soft room warmth
    b_lp, a_lp = signal.butter(2, 400 / (sr / 2), btype='low')
    room_tone = signal.filtfilt(b_lp, a_lp, unequal_noise)
    room_tone /= (np.max(np.abs(room_tone)) + 1e-6)
    room_tone *= 10 ** (-52.0 / 20.0) # -52 dBFS soft warm room bed

    # Mix clean speech with steady room bed
    mixed_audio = data + room_tone

    # Normalize
    max_p = np.max(np.abs(mixed_audio))
    if max_p > 0:
        mixed_audio = mixed_audio * (0.891 / max_p)

    out_file = AUDIO_DIR / "sample_13_veda_rami_steady_room_bed.mp3"
    sf.write(str(out_file), mixed_audio, sr)
    print(f"[COMPLETE] Steady Room Bed Sample Saved: {out_file}")

if __name__ == "__main__":
    process_comfort_noise()
