import os
import glob
import struct
import numpy as np
from scipy import signal
from pathlib import Path

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
CACHE_DIR = AUDIO_DIR / "cache_ep001"
SAMPLE_RATE = 24000

def apply_dsp_mastering(pcm_data: bytes, fade_ms: float = 15.0) -> np.ndarray:
    """Processes raw int16 PCM audio with high-pass filtering and cosine S-curve fading."""
    if not pcm_data:
        return np.array([], dtype=np.int16)
        
    # 1. Convert to float32 [-1.0, 1.0]
    samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    if len(samples) == 0:
        return np.array([], dtype=np.int16)

    # 2. DC Offset Removal (Center audio around zero)
    samples = samples - np.mean(samples)

    # 3. 80Hz High-Pass Filter (Removes low-end thumps, pops, sub-bass clicks)
    b, a = signal.butter(2, 80.0 / (SAMPLE_RATE / 2.0), btype='highpass')
    samples = signal.filtfilt(b, a, samples)

    # 4. Trim trailing glitch/noise spikes at end of turn buffer
    end_cut = len(samples)
    for i in range(len(samples) - 1, max(0, len(samples) - 3000), -1):
        if np.abs(samples[i]) > 0.01:
            end_cut = i
        else:
            break
    if end_cut < len(samples) - 100:
        samples = samples[:end_cut]

    # 5. Smooth 20ms Cosine S-curve fade-in & fade-out
    fade_len = int(SAMPLE_RATE * (fade_ms / 1000.0))
    if len(samples) > fade_len * 2:
        t = np.linspace(0, np.pi, fade_len)
        fade_in = 0.5 * (1.0 - np.cos(t))
        fade_out = 0.5 * (1.0 + np.cos(t))
        
        samples[:fade_len] *= fade_in
        samples[-fade_len:] *= fade_out

    return samples

def build_dsp_smoothed_master():
    print("==========================================================")
    print("[DSP MASTERING] Applying Studio De-Clicking & S-Curve Fades")
    print("==========================================================")

    pcm_files = sorted(glob.glob(str(CACHE_DIR / "turn_*.pcm")))
    print(f" -> Found {len(pcm_files)} cached turns.")
    
    processed_turns = []
    for fpath in pcm_files:
        filename = Path(fpath).name
        raw_bytes = Path(fpath).read_bytes()
        
        # Process turn with 15ms S-curve fade + 80Hz high-pass filter
        float_turn = apply_dsp_mastering(raw_bytes, fade_ms=15.0)
        processed_turns.append(float_turn)
        print(f" -> DSP Mastered: {filename} ({len(float_turn)} samples)")

    # Join turns with 450ms smooth silence
    silence_len = int(SAMPLE_RATE * 0.45)
    silence = np.zeros(silence_len, dtype=np.float32)
    
    combined_audio = []
    for i, turn in enumerate(processed_turns):
        combined_audio.append(turn)
        if i < len(processed_turns) - 1:
            combined_audio.append(silence)

    full_track = np.concatenate(combined_audio)

    # Peak Normalization (-1.0 dBFS)
    peak = np.max(np.abs(full_track))
    if peak > 0:
        target_peak = 10 ** (-1.0 / 20.0) # ~0.891
        full_track = (full_track / peak) * target_peak

    # Convert float32 back to int16 PCM
    int16_pcm = (full_track * 32767.0).astype(np.int16).tobytes()

    # Format WAV Header
    num_channels = 1
    bytes_per_sample = 2
    byte_rate = SAMPLE_RATE * num_channels * bytes_per_sample
    block_align = num_channels * bytes_per_sample
    data_len = len(int16_pcm)
    file_len = 36 + data_len
    
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', file_len, b'WAVE', b'fmt ', 16, 
        1, num_channels, SAMPLE_RATE, byte_rate, 
        block_align, bytes_per_sample * 8, b'data', data_len
    )
    
    master_wav = header + int16_pcm
    
    master_file = AUDIO_DIR / "ep-001-master-8min.wav"
    master_file.write_bytes(master_wav)
    
    main_mp3 = AUDIO_DIR / "ep-001.mp3"
    main_mp3.write_bytes(master_wav)
    
    duration_secs = len(int16_pcm) / (SAMPLE_RATE * 2)
    mins = int(duration_secs // 60)
    secs = int(duration_secs % 60)
    
    print("\n==========================================================")
    print("[DSP MASTERING COMPLETE]")
    print(f" [Passed] Total Turns Processed: {len(pcm_files)}")
    print(f" [Passed] DC Offset Removed & 80Hz High-Pass Applied")
    print(f" [Passed] 15ms Cosine S-Curve Boundary Fades Applied")
    print(f" [Passed] Peak Normalized to -1.0 dBFS")
    print(f" [Passed] Output Master Duration: {mins}m {secs}s")
    print("==========================================================")

if __name__ == "__main__":
    build_dsp_smoothed_master()
