import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

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

def build_mini_4turn_sample():
    in_wav = AUDIO_DIR / "sample_17_weekend_recap_zero_kshhh.wav"
    if not in_wav.exists():
        print("Source WAV not found!")
        return

    data, sr = sf.read(str(in_wav))
    if data.ndim > 1: data = np.mean(data, axis=1)

    print("==========================================================")
    print("Building 4-Turn Mini Sample with Zero-Crossing Alignment")
    print("==========================================================")

    # Main gap boundaries for Turn 1, Turn 2, Turn 3, Turn 4
    # (extracted from RMS energy analysis of sample_17)
    turns = [
        data[0 : 400800],           # Turn 1 (Veda)
        data[415200 : 664800],       # Turn 2 (Rami)
        data[674400 : 849600],       # Turn 3 (Veda)
        data[864000 : 1156800]       # Turn 4 (Rami)
    ]

    # 80Hz High Pass Filter
    b_hp, a_hp = signal.butter(2, 80 / (sr / 2), btype='high')

    cleaned_turns = []
    silence_gap = np.zeros(int(sr * 0.35), dtype=np.float32) # 350ms gap

    for idx, turn_samples in enumerate(turns):
        turn_samples = signal.filtfilt(b_hp, a_hp, turn_samples)
        
        # Calculate 10ms RMS
        win_len = int(sr * 0.01)
        num_wins = len(turn_samples) // win_len
        rms_arr = np.array([np.sqrt(np.mean(turn_samples[i*win_len : (i+1)*win_len]**2)) for i in range(num_wins)])

        speech_wins = np.where(rms_arr > 0.008)[0]
        if len(speech_wins) == 0:
            cleaned_turns.append(turn_samples)
            cleaned_turns.append(silence_gap)
            continue

        first_speech_idx = max(0, (speech_wins[0] - 2) * win_len)
        
        # Natural decay: keep up to 80ms after speech drops below 0.002
        quiet_wins = np.where(rms_arr < 0.002)[0]
        tail_quiet = quiet_wins[quiet_wins > speech_wins[-1]]
        
        if len(tail_quiet) > 0:
            raw_cut_idx = tail_quiet[0] * win_len + int(sr * 0.08)
        else:
            raw_cut_idx = (speech_wins[-1] + 4) * win_len

        raw_cut_idx = min(len(turn_samples), raw_cut_idx)

        # Align start & end to exact zero crossings (0.0V)
        start_zc = find_nearest_zero_crossing(turn_samples, first_speech_idx)
        end_zc = find_nearest_zero_crossing(turn_samples, raw_cut_idx)

        trimmed = turn_samples[start_zc:end_zc]

        # Apply 30ms Cosine S-curve decay fade
        fade_len = int(sr * 0.03) # 30ms
        if len(trimmed) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            trimmed[:fade_len] *= fade_in
            trimmed[-fade_len:] *= fade_out

        print(f" -> Turn {idx+1}: Trimmed from {len(turn_samples)} to {len(trimmed)} samples (Zero-crossing aligned)")
        cleaned_turns.append(trimmed)
        cleaned_turns.append(silence_gap)

    full_clean = np.concatenate(cleaned_turns)

    # Peak normalize to -1.0 dBFS
    max_p = np.max(np.abs(full_clean))
    if max_p > 0: full_clean = full_clean * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_22_mini_4turn_zero_noise.mp3"
    out_wav = AUDIO_DIR / "sample_22_mini_4turn_zero_noise.wav"

    sf.write(str(out_wav), full_clean, sr)
    sf.write(str(out_mp3), full_clean, sr)

    duration = len(full_clean) / sr
    print("==========================================================")
    print(f"[COMPLETE] Saved Mini Sample 22: {out_mp3}")
    print(f"Duration: {duration:.2f}s (4 turns, 3 transitions)")
    print("==========================================================")

if __name__ == "__main__":
    build_mini_4turn_sample()
