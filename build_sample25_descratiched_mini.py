import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def de_scratch_tail(samples, sr=24000):
    """Surgically filters high-frequency sibilance/friction scratch at sentence ends."""
    tail_len = int(sr * 0.20) # 200ms
    if len(samples) < tail_len * 2:
        return samples

    head = samples[:-tail_len]
    tail = samples[-tail_len:]

    # 5.5kHz Low Pass filter on tail to eliminate high-frequency friction scratch
    b_lp, a_lp = signal.butter(2, 5500 / (sr / 2), btype='low')
    clean_tail = signal.filtfilt(b_lp, a_lp, tail)

    # Smooth 30ms crossfade
    xfade_len = int(sr * 0.03)
    fade_out = np.linspace(1.0, 0.0, xfade_len)
    fade_in = np.linspace(0.0, 1.0, xfade_len)

    head[-xfade_len:] = head[-xfade_len:] * fade_out + clean_tail[:xfade_len] * fade_in
    return np.concatenate([head, clean_tail[xfade_len:]])

def build_sample25():
    in_wav = AUDIO_DIR / "sample_22_mini_4turn_zero_noise.wav"
    if not in_wav.exists():
        print("Sample 22 WAV not found!")
        return

    data, sr = sf.read(str(in_wav))
    if data.ndim > 1: data = np.mean(data, axis=1)

    print("==========================================================")
    print("Building Sample 25: De-Scratched Tail 4-Turn Mini Sample")
    print("==========================================================")

    # Extract 4 turns
    turns = [
        data[0 : 394801],
        data[415200 : 664800],
        data[674400 : 849600],
        data[864000 : 1156800]
    ]

    cleaned_turns = []
    silence_gap = np.zeros(int(sr * 0.35), dtype=np.float32)

    for idx, turn_samples in enumerate(turns):
        descratiched = de_scratch_tail(turn_samples, sr)
        print(f" -> Turn {idx+1}: De-scratched sentence-final high frequencies.")
        cleaned_turns.append(descratiched)
        cleaned_turns.append(silence_gap)

    full_track = np.concatenate(cleaned_turns)
    max_p = np.max(np.abs(full_track))
    if max_p > 0: full_track = full_track * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_25_descratiched_4turn_mini.mp3"
    out_wav = AUDIO_DIR / "sample_25_descratiched_4turn_mini.wav"

    sf.write(str(out_wav), full_track, sr)
    sf.write(str(out_mp3), full_track, sr)

    print("==========================================================")
    print(f"[COMPLETE] Saved Sample 25: {out_mp3}")
    print("==========================================================")

if __name__ == "__main__":
    build_sample25()
