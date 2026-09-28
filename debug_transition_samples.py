import os
import numpy as np
import soundfile as sf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def inspect_transitions():
    file_path = AUDIO_DIR / "sample_11_veda_rami_natural_clean.mp3"
    if not file_path.exists():
        print("File not found")
        return

    data, sr = sf.read(str(file_path))
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    print(f"Total duration: {len(data)/sr:.2f}s ({len(data)} samples)")

    # Find regions of near-zero energy (the 400ms gaps between turns)
    # Energy in 20ms windows (480 samples)
    win_len = int(sr * 0.02)
    energies = []
    for i in range(0, len(data) - win_len, win_len):
        chunk = data[i:i+win_len]
        rms = np.sqrt(np.mean(chunk**2))
        energies.append((i, i+win_len, rms))

    print("\n--- Silence / Low-energy Window Regions ---")
    for start, end, rms in energies:
        db = 20 * np.log10(rms + 1e-9)
        if db < -35:
            start_s = start / sr
            end_s = end / sr
            print(f"Gap at {start_s:.3f}s - {end_s:.3f}s | RMS: {rms:.6f} ({db:.1f} dBFS)")

if __name__ == "__main__":
    inspect_transitions()
