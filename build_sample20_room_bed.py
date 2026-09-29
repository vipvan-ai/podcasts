import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def process_sample_20():
    in_wav = AUDIO_DIR / "sample_19_spectral_denoised_zero_kshhh.wav"
    if not in_wav.exists():
        print("Sample 19 WAV not found!")
        return

    data, sr = sf.read(str(in_wav))
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    print("==========================================================")
    print("Building Sample 20: Spectral Denoised + Studio Room Bed")
    print("==========================================================")

    # Generate continuous warm studio room noise at -50 dBFS
    num_samples = len(data)
    np.random.seed(42)
    noise = np.random.randn(num_samples).astype(np.float32)
    
    # 350Hz low-pass filter to give room tone warm acoustic feel
    b_lp, a_lp = signal.butter(2, 350 / (sr / 2), btype='low')
    room_tone = signal.filtfilt(b_lp, a_lp, noise)
    room_tone /= (np.max(np.abs(room_tone)) + 1e-6)
    room_tone *= 10 ** (-50.0 / 20.0) # -50 dBFS warm room bed

    mixed = data + room_tone

    # Peak normalize
    max_p = np.max(np.abs(mixed))
    if max_p > 0:
        mixed = mixed * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_20_spectral_denoised_studio_room_bed.mp3"
    out_wav = AUDIO_DIR / "sample_20_spectral_denoised_studio_room_bed.wav"

    sf.write(str(out_wav), mixed, sr)
    sf.write(str(out_mp3), mixed, sr)

    print("==========================================================")
    print(f"[COMPLETE] Saved Sample 20: {out_mp3}")
    print(f"Duration: {len(mixed)/sr:.2f}s")
    print("==========================================================")

if __name__ == "__main__":
    process_sample_20()
