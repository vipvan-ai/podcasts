import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def build_mini_23_room_bed():
    in_wav = AUDIO_DIR / "sample_22_mini_4turn_zero_noise.wav"
    if not in_wav.exists():
        print("Sample 22 WAV not found!")
        return

    data, sr = sf.read(str(in_wav))
    if data.ndim > 1: data = np.mean(data, axis=1)

    print("==========================================================")
    print("Building Mini Sample 23: Zero-Crossing + Studio Room Bed")
    print("==========================================================")

    # Generate continuous warm studio room tone at -50 dBFS
    num_samples = len(data)
    np.random.seed(42)
    noise = np.random.randn(num_samples).astype(np.float32)
    
    b_lp, a_lp = signal.butter(2, 350 / (sr / 2), btype='low')
    room_tone = signal.filtfilt(b_lp, a_lp, noise)
    room_tone /= (np.max(np.abs(room_tone)) + 1e-6)
    room_tone *= 10 ** (-50.0 / 20.0) # -50 dBFS soft warm room bed

    mixed = data + room_tone
    max_p = np.max(np.abs(mixed))
    if max_p > 0: mixed = mixed * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_23_mini_4turn_room_bed.mp3"
    out_wav = AUDIO_DIR / "sample_23_mini_4turn_room_bed.wav"

    sf.write(str(out_wav), mixed, sr)
    sf.write(str(out_mp3), mixed, sr)

    print("==========================================================")
    print(f"[COMPLETE] Saved Mini Sample 23: {out_mp3}")
    print(f"Duration: {len(mixed)/sr:.2f}s (4 turns, 3 transitions)")
    print("==========================================================")

if __name__ == "__main__":
    build_mini_23_room_bed()
