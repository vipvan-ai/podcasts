import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def fix_existing_recap_bursts():
    in_wav = AUDIO_DIR / "sample_17_weekend_recap_zero_kshhh.wav"
    if not in_wav.exists():
        print("Source WAV not found!")
        return

    data, sr = sf.read(str(in_wav))
    if data.ndim > 1: data = np.mean(data, axis=1)

    print("==========================================================")
    print("Surgically Stripping Gemini Buffer Bursts from Sample 17")
    print("==========================================================")

    # 1. Split audio by silence gaps (where np.abs(data) < 0.0001)
    is_speech = np.abs(data) > 0.0001
    
    # 2. Group into contiguous speech blocks separated by > 200ms silence (4800 samples)
    min_silence_len = int(sr * 0.20)
    
    # Find start and end indices of speech blocks
    diff = np.diff(is_speech.astype(int))
    starts = list(np.where(diff == 1)[0] + 1)
    ends = list(np.where(diff == -1)[0])

    if is_speech[0]: starts.insert(0, 0)
    if is_speech[-1]: ends.append(len(data)-1)

    # Merge blocks that are separated by less than min_silence_len (intra-turn pauses)
    merged_blocks = []
    curr_start = starts[0]
    curr_end = ends[0]

    for s, e in zip(starts[1:], ends[1:]):
        if s - curr_end < min_silence_len:
            curr_end = e
        else:
            merged_blocks.append((curr_start, curr_end))
            curr_start = s
            curr_end = e
    merged_blocks.append((curr_start, curr_end))

    print(f" -> Found {len(merged_blocks)} turns in the audio.")

    cleaned_turns = []
    silence_gap = np.zeros(int(sr * 0.38), dtype=np.float32)

    for idx, (b_start, b_end) in enumerate(merged_blocks):
        turn_samples = data[b_start:b_end]
        
        # Check last 300ms (7200 samples) of turn_samples for maximum amplitude spike / burst
        if len(turn_samples) > 7200:
            tail_chunk = turn_samples[-7200:]
            # 10ms RMS windowing
            win_10ms = int(sr * 0.01)
            num_w = len(tail_chunk) // win_10ms
            rms_list = [np.sqrt(np.mean(tail_chunk[w*win_10ms : (w+1)*win_10ms]**2)) for w in range(num_w)]
            
            # Find if there is a burst (> 0.04) preceded by low energy (< 0.005)
            cut_idx = len(turn_samples)
            for w in range(num_w - 1, 2, -1):
                if rms_list[w] > 0.04 and np.max(rms_list[max(0, w-5):w]) < 0.005:
                    # Cut point identified at start of burst!
                    cut_offset = (w - 1) * win_10ms
                    cut_idx = (len(turn_samples) - 7200) + cut_offset
                    print(f"    Turn {idx+1}: Stripped tail burst of {len(turn_samples) - cut_idx} samples (~{(len(turn_samples) - cut_idx)/sr*1000:.1f}ms)")
                    break
            
            turn_samples = turn_samples[:cut_idx]

        # Apply 20ms Cosine S-curve fade in/out
        fade_len = int(sr * 0.02)
        if len(turn_samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            turn_samples[:fade_len] *= fade_in
            turn_samples[-fade_len:] *= fade_out

        cleaned_turns.append(turn_samples)
        cleaned_turns.append(silence_gap)

    full_clean = np.concatenate(cleaned_turns)

    # 80Hz High Pass Filter
    b, a = signal.butter(2, 80 / (sr / 2), btype='high')
    full_clean = signal.filtfilt(b, a, full_clean)

    # Peak normalize
    max_p = np.max(np.abs(full_clean))
    if max_p > 0: full_clean = full_clean * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_21_veda_rami_zero_bursts.mp3"
    out_wav = AUDIO_DIR / "sample_21_veda_rami_zero_bursts.wav"

    sf.write(str(out_wav), full_clean, sr)
    sf.write(str(out_mp3), full_clean, sr)

    print("==========================================================")
    print(f"[COMPLETE] Saved Sample 21: {out_mp3}")
    print(f"Duration: {len(full_clean)/sr:.2f}s")
    print("==========================================================")

if __name__ == "__main__":
    fix_existing_recap_bursts()
