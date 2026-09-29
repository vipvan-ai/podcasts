import asyncio
import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path
import edge_tts

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

MINI_SCRIPT_EDGE = [
    {
        "speaker": "Veda",
        "voice": "en-US-AvaNeural",
        "text": "Happy weekend, everyone! Welcome to the Future Human Daily Weekend Recap. Alex and Elena are off taking a well-deserved break today and will be back bright and early Monday morning—so I am Veda with Rami, and we are kicking back with your Saturday morning coffee."
    },
    {
        "speaker": "Rami",
        "voice": "en-US-AndrewNeural",
        "text": "That is right! No heavy quantum physics equations today, folks. Just pure weekend vibes and the funniest, wildest tech stories that broke this week."
    },
    {
        "speaker": "Veda",
        "voice": "en-US-AvaNeural",
        "text": "Speaking of wild, Rami... did you catch that video of the new humanoid robot trying to fold laundry?"
    },
    {
        "speaker": "Rami",
        "voice": "en-US-AndrewNeural",
        "text": "Oh, I replayed it three times! It took five minutes to fold one t-shirt, and then accidentally threw the matching sock across the living room! Honestly, that is still better than my college roommate used to do."
    }
]

async def synth_turn(text, voice, out_mp3):
    for attempt in range(5):
        try:
            communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
            await communicate.save(str(out_mp3))
            if out_mp3.exists() and out_mp3.stat().st_size > 1000:
                return True
        except Exception as e:
            print(f"    Edge retry {attempt+1}... ({e})")
            await asyncio.sleep(2)
    return False

async def build_edge_mini_sample():
    print("==========================================================")
    print("Generating 4-Turn Edge-TTS Mini Sample (Veda & Rami)")
    print("==========================================================")

    sample_rate = 24000
    combined_chunks = []
    silence_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    b_hp, a_hp = signal.butter(2, 80 / (sample_rate / 2), btype='high')

    for idx, turn in enumerate(MINI_SCRIPT_EDGE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        tmp_mp3 = AUDIO_DIR / f"tmp_edge_{idx+1}.mp3"

        print(f" -> Generating Turn {idx+1}/4 [{speaker} ({voice})]: {text[:45]}...")
        ok = await synth_turn(text, voice, tmp_mp3)

        if not ok or not tmp_mp3.exists():
            print(f"Failed turn {idx+1}")
            continue

        data, sr = sf.read(str(tmp_mp3))
        if data.ndim > 1: data = np.mean(data, axis=1)

        if sr != sample_rate:
            num_samples = int(len(data) * sample_rate / sr)
            data = signal.resample(data, num_samples)

        data = signal.filtfilt(b_hp, a_hp, data)

        fade_len = int(sample_rate * 0.02)
        if len(data) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            data[:fade_len] *= fade_in
            data[-fade_len:] *= fade_out

        combined_chunks.append(data)
        combined_chunks.append(silence_gap)

        if tmp_mp3.exists(): tmp_mp3.unlink()

    if not combined_chunks:
        print("[Error] No audio chunks generated.")
        return

    full_track = np.concatenate(combined_chunks)
    max_p = np.max(np.abs(full_track))
    if max_p > 0: full_track = full_track * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_28_mini_edge_tts_veda_rami.mp3"
    out_wav = AUDIO_DIR / "sample_28_mini_edge_tts_veda_rami.wav"

    sf.write(str(out_wav), full_track, sample_rate)
    sf.write(str(out_mp3), full_track, sample_rate)

    duration = len(full_track) / sample_rate
    print("==========================================================")
    print(f"[COMPLETE] Saved Edge-TTS Sample 28: {out_mp3}")
    print(f"Duration: {duration:.2f}s (4 turns, 3 transitions)")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(build_edge_mini_sample())
