import os
import sys
import time
import base64
import numpy as np
import scipy.signal as signal
from scipy.signal import butter, sosfilt
import soundfile as sf
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types

from generate_weekend_script import get_weekend_script

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

TTS_MODELS = [
    'gemini-3.8-flash-tts',
    'gemini-3.8-flash-lite-tts',
    'gemini-3.1-flash-tts-preview',
    'gemini-2.5-flash-preview-tts'
]

def clean_turn(x, sr=24000, gap_ms=60, max_artifact_ms=250, flat_thresh=0.3):
    """Spectral Flatness Measure & Active Energy Run Grouping algorithm."""
    x = np.asarray(x)
    if x.dtype == np.int16:
        x = x.astype(np.float32) / 32768.0
    x = x.astype(np.float32) - x.mean()                 # remove DC

    hp = sosfilt(butter(4, 80, 'hp', fs=sr, output='sos'), x)
    fl = int(0.010 * sr)                                # 10 ms frames
    n = len(hp) // fl
    if n == 0: return x
    fr = hp[:n * fl].reshape(n, fl)

    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    active = db > (np.percentile(db, 95) - 35)

    spec = np.abs(np.fft.rfft(fr * np.hanning(fl), axis=1)) + 1e-9
    flat = np.exp(np.log(spec).mean(1)) / spec.mean(1)  # spectral flatness

    runs, s, last = [], None, None
    gap = gap_ms // 10
    for i, a in enumerate(active):
        if a:
            if s is None: s = i
            last = i
        elif s is not None and i - last > gap:
            runs.append((s, last + 1)); s = None
    if s is not None: runs.append((s, last + 1))
    if not runs: return x

    # drop trailing short, noise-like runs (the "kshhh" / tail burst)
    while len(runs) > 1:
        a, b = runs[-1]
        if (b - a) * 10 < max_artifact_ms and flat[a:b].mean() > flat_thresh:
            runs.pop()
        else:
            break

    start = max(0, runs[0][0] * fl - int(0.03 * sr))
    end = min(len(x), runs[-1][1] * fl + int(0.06 * sr))  # keep natural vocal decay
    y = x[start:end].copy()

    fi, fo = int(0.008 * sr), int(0.05 * sr)              # short fade in, longer fade out
    if len(y) > fi + fo:
        y[:fi] *= np.linspace(0, 1, fi)
        y[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    return y

def apply_studio_warmth_eq(audio_samples, sample_rate=24000, low_boost_db=4.0):
    """Broadcast Studio Proximity Warmth EQ Pass (+4.0 dB @ 150Hz)."""
    f0 = 150.0
    Q = 0.9
    gain_db = low_boost_db
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / sample_rate
    alpha = np.sin(w0) / (2 * Q)
    
    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A

    b_eq = np.array([b0, b1, b2]) / a0
    a_eq = np.array([a0, a1, a2]) / a0

    return signal.filtfilt(b_eq, a_eq, audio_samples)

def update_weekend_rss(day_name, ep_title, ep_summary, mp3_filename, duration_str, file_size_bytes):
    rss_file = BASE_DIR / "rss.xml"
    if not rss_file.exists():
        print("[Warning] rss.xml not found, skipping RSS update.")
        return

    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    guid = f"future-human-daily-weekend-{day_name.lower()}-{datetime.now().strftime('%Y%m%d')}"

    item_xml = f"""    <!-- WEEKEND RECAP: {day_name.upper()} -->
    <item>
      <title>{ep_title}</title>
      <itunes:title>{ep_title}</itunes:title>
      <itunes:episodeType>bonus</itunes:episodeType>
      <itunes:author>Veda &amp; Rami</itunes:author>
      <itunes:summary>{ep_summary}</itunes:summary>
      <description><![CDATA[
        <p>Welcome to the Future Human Daily Weekend Recap hosted by Veda and Rami!</p>
        <p>{ep_summary}</p>
      ]]></description>
      <enclosure url="https://vipvan-ai.github.io/podcasts/audio/{mp3_filename}" length="{file_size_bytes}" type="audio/mpeg" />
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>no</itunes:explicit>
    </item>
"""

    if "<channel>" in content and "<!-- EPISODE" in content:
        insert_pos = content.find("<!-- EPISODE")
        updated = content[:insert_pos] + item_xml + "\n" + content[insert_pos:]
        rss_file.write_text(updated, encoding="utf-8")
        print(f"[RSS UPDATE] Added {day_name} Weekend Recap to rss.xml!")

def build_weekend_recap_pipeline(is_sunday=False):
    sample_rate = 24000
    day_name = "Sunday" if is_sunday else "Saturday"
    tag_suffix = "sun" if is_sunday else "sat"
    date_str = datetime.now().strftime("%B %d, %Y")

    print("==========================================================", flush=True)
    print(f"Building Future Human Daily - {day_name} Weekend Recap ({date_str})", flush=True)
    print("Hosts: Veda & Rami | Target: ~10 Minutes (30 Turns)", flush=True)
    print("==========================================================", flush=True)

    cache_dir = AUDIO_DIR / f"cache_weekend_{tag_suffix}"
    cache_dir.mkdir(parents=True, exist_ok=True)

    script = get_weekend_script(is_sunday=is_sunday)
    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32) # 350ms natural pause

    for idx, turn in enumerate(script):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        cache_file = cache_dir / f"turn_{idx+1:02d}_{speaker}.npy"

        raw_samples = None
        if cache_file.exists():
            print(f" -> Turn {idx+1}/{len(script)} [{speaker}] loaded from CACHE", flush=True)
            raw_samples = np.load(str(cache_file))
        else:
            print(f" -> Synthesizing Turn {idx+1}/{len(script)} [{speaker} ({voice})]: {text[:45]}...", flush=True)
            success = False
            for attempt in range(10):
                for model_name in TTS_MODELS:
                    try:
                        resp = client.models.generate_content(
                            model=model_name,
                            contents=text,
                            config=types.GenerateContentConfig(
                                response_modalities=["AUDIO"],
                                speech_config=types.SpeechConfig(
                                    voice_config=types.VoiceConfig(
                                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                                    )
                                )
                            )
                        )
                        part = resp.candidates[0].content.parts[0]
                        if part.inline_data:
                            data = part.inline_data.data
                            if isinstance(data, str): data = base64.b64decode(data)
                            raw_samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                            np.save(str(cache_file), raw_samples)
                            print(f"    [Success ({model_name})] Cached {len(raw_samples)} samples.", flush=True)
                            success = True
                            time.sleep(2)
                            break
                    except Exception as e:
                        print(f"    [Model Fallback ({model_name})] Quota/Rate limit, waiting 4s...", flush=True)
                        time.sleep(4)
                if success:
                    break
                print(f"    [Retry Attempt {attempt+1}/10] All models rate limited. Sleeping 10s...", flush=True)
                time.sleep(10)

            if not success:
                print(f"    [Warning] All models exhausted for turn {idx+1}. Using synthetic zero pad.", flush=True)
                raw_samples = np.zeros(int(sample_rate * 2.0), dtype=np.float32)

        if raw_samples is not None:
            # 1. Clean Turn (SFM tail noise drop)
            cleaned = clean_turn(raw_samples, sample_rate)

            # 2. Apply Studio Warmth EQ (+4.0 dB @ 150 Hz)
            warmed = apply_studio_warmth_eq(cleaned, sample_rate)

            audio_chunks.append(warmed)
            audio_chunks.append(pause_gap)

    if not audio_chunks:
        print("[Error] No audio chunks synthesized!")
        return False

    # Concatenate turns
    speech_track = np.concatenate(audio_chunks)

    # 3. Create Continuous Studio Room Tone Bed (-52 dBFS noise floor)
    total_len = len(speech_track)
    np.random.seed(42)
    room_noise = np.random.normal(0, 1.0, total_len).astype(np.float32)
    # Bandpass filter room tone between 120Hz and 3500Hz for warm room acoustics
    b_room, a_room = signal.butter(2, [120 / (sample_rate / 2), 3500 / (sample_rate / 2)], btype='band')
    filtered_room = signal.filtfilt(b_room, a_room, room_noise)
    room_target_amp = 10 ** (-52.0 / 20.0) # ~0.00251
    filtered_room = filtered_room * (room_target_amp / (np.max(np.abs(filtered_room)) + 1e-9))

    # Mix speech track with continuous room bed
    mixed_audio = speech_track + filtered_room

    # 4. Peak Normalization to -1.0 dBFS (0.89125)
    max_peak = np.max(np.abs(mixed_audio))
    if max_peak > 0:
        target_peak = 10 ** (-1.0 / 20.0)
        mixed_audio = mixed_audio * (target_peak / max_peak)

    out_mp3_name = f"ep-weekend-{tag_suffix}.mp3"
    out_wav_name = f"ep-weekend-{tag_suffix}.wav"
    out_mp3 = AUDIO_DIR / out_mp3_name
    out_wav = AUDIO_DIR / out_wav_name

    sf.write(str(out_wav), mixed_audio, sample_rate)
    sf.write(str(out_mp3), mixed_audio, sample_rate)

    duration_sec = len(mixed_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes:02d}:{seconds:02d}"

    print("==========================================================", flush=True)
    print(f"[SUCCESS] Mastered {day_name} Weekend Recap!", flush=True)
    print(f"Duration: {minutes}m {seconds}s ({duration_sec:.2f}s)", flush=True)
    print(f"Output MP3: {out_mp3}", flush=True)
    print("==========================================================", flush=True)

    # Update RSS feed
    ep_title = f"{day_name} Weekend Recap: Tech Deep Dives & Weekly Catchup" if not is_sunday else "Sunday AI Catchup: Claude Opus 5.5 & Cyber Defense"
    ep_summary = "Veda & Rami host a relaxed weekend recap featuring deep tech stories, unhurried pacing, and zero noise transitions."
    file_size = out_mp3.stat().st_size if out_mp3.exists() else 0
    update_weekend_rss(day_name, ep_title, ep_summary, out_mp3_name, duration_str, file_size)

    # Auto-publish to GitHub Pages and Spotify RSS
    publish_to_github(f"Auto-publish {day_name} Weekend Recap ({date_str})")

    return True

def publish_to_github(commit_message):
    import subprocess
    try:
        print("[GIT PUBLISH] Staging updated RSS feed and episode audio...", flush=True)
        subprocess.run(["git", "add", "index.html", "rss.xml", "audio/", "*.py"], cwd=str(BASE_DIR), check=True)
        print(f"[GIT PUBLISH] Committing: {commit_message}", flush=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=str(BASE_DIR), check=False)
        print("[GIT PUBLISH] Pushing to origin master...", flush=True)
        res = subprocess.run(["git", "push", "origin", "master"], cwd=str(BASE_DIR), capture_output=True, text=True)
        if res.returncode == 0:
            print("[GIT PUBLISH SUCCESS] Episode published to GitHub Pages & Spotify RSS!", flush=True)
        else:
            print(f"[GIT PUBLISH WARNING] Push output: {res.stderr}", flush=True)
    except Exception as e:
        print(f"[GIT PUBLISH ERROR] Failed to auto-publish: {e}", flush=True)

if __name__ == "__main__":
    is_sun = "--sunday" in sys.argv
    build_weekend_recap_pipeline(is_sunday=is_sun)
