import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def process_chopped_samples():
    in_wav = AUDIO_DIR / "sample_22_mini_4turn_zero_noise.wav"
    if not in_wav.exists():
        print("Sample 22 WAV not found!")
        return

    data, sr = sf.read(str(in_wav))
    if data.ndim > 1: data = np.mean(data, axis=1)

    print("==========================================================")
    print("Building Tail-Chopped Solo & 4-Turn Mini Dialogue Samples")
    print("==========================================================")

    # Find the speech bounds for Turn 1 (Veda) and Turn 2 (Rami)
    # Turn 1: sample 0 to 394801
    # Turn 2: sample 415200 to 664800
    # Turn 3: sample 674400 to 849600
    # Turn 4: sample 864000 to 1156800

    raw_turns = [
        data[0 : 394801],
        data[415200 : 664800],
        data[674400 : 849600],
        data[864000 : 1156800]
    ]

    cleaned_turns = []
    silence_gap = np.zeros(int(sr * 0.35), dtype=np.float32)

    for idx, turn in enumerate(raw_turns):
        if len(turn) < 4800: continue
        
        # 1. High Pass Filter at 80Hz
        b, a = signal.butter(2, 80 / (sr / 2), btype='high')
        turn = signal.filtfilt(b, a, turn)

        # 2. Chop off the trailing 150ms (3600 samples) where Gemini's API tail noise lives!
        # And find speech energy end before the chop point
        win_10ms = int(sr * 0.01)
        num_w = len(turn) // win_10ms
        rms_vals = np.array([np.sqrt(np.mean(turn[i*win_10ms:(i+1)*win_10ms]**2)) for i in range(num_w)])
        
        speech_w = np.where(rms_vals > 0.008)[0]
        if len(speech_w) > 0:
            last_speech_sample = (speech_w[-1] + 2) * win_10ms # Keep 20ms after last speech
            cut_sample = min(len(turn), last_speech_sample)
        else:
            cut_sample = len(turn) - 3600

        chopped_turn = turn[:cut_sample].copy()

        # 3. Apply 25ms Cosine S-curve fade out to the chopped end
        fade_len = int(sr * 0.025)
        if len(chopped_turn) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            chopped_turn[:fade_len] *= fade_in
            chopped_turn[-fade_len:] *= fade_out

        print(f" -> Turn {idx+1}: Trimmed tail from {len(turn)} to {len(chopped_turn)} samples (Chopped trailing {len(turn)-len(chopped_turn)} tail samples)")
        cleaned_turns.append(chopped_turn)

        # Save Solo Veda (Turn 1) and Solo Rami (Turn 2)
        if idx == 0:
            sf.write(str(AUDIO_DIR / "test_veda_solo_tail_chopped.wav"), chopped_turn, sr)
            sf.write(str(AUDIO_DIR / "test_veda_solo_tail_chopped.mp3"), chopped_turn, sr)
        elif idx == 1:
            sf.write(str(AUDIO_DIR / "test_rami_solo_tail_chopped.wav"), chopped_turn, sr)
            sf.write(str(AUDIO_DIR / "test_rami_solo_tail_chopped.mp3"), chopped_turn, sr)

    # Build full 4-turn dialogue track with silence gaps
    dialogue_chunks = []
    for turn in cleaned_turns:
        dialogue_chunks.append(turn)
        dialogue_chunks.append(silence_gap)

    full_dialogue = np.concatenate(dialogue_chunks)
    max_p = np.max(np.abs(full_dialogue))
    if max_p > 0: full_dialogue = full_dialogue * (0.891 / max_p)

    out_wav = AUDIO_DIR / "sample_26_mini_4turn_tail_chopped.wav"
    out_mp3 = AUDIO_DIR / "sample_26_mini_4turn_tail_chopped.mp3"

    sf.write(str(out_wav), full_dialogue, sr)
    sf.write(str(out_mp3), full_dialogue, sr)

    print("==========================================================")
    print(f"[COMPLETE] Saved Sample 26: {out_mp3}")
    print("==========================================================")

if __name__ == "__main__":
    process_chopped_samples()
