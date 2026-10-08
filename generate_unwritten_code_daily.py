import os
import sys
import time
import base64
import subprocess
import re
import asyncio
import edge_tts
import numpy as np
import scipy.signal as signal
from scipy.signal import butter, sosfilt
import soundfile as sf
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = AUDIO_DIR / "unwritten_code_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load .env
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

TTS_MODELS = [
    'gemini-3.8-flash-tts',
    'gemini-3.8-flash-lite-tts',
    'gemini-2.5-flash-preview-tts',
    'gemini-3.1-flash-tts-preview'
]

EDGE_VOICES = {
    "Kore": "en-US-AriaNeural",
    "Puck": "en-US-GuyNeural",
    "Maya": "en-US-AriaNeural",
    "Julian": "en-US-GuyNeural"
}

def synth_edge_turn(text, voice_key, sample_rate=24000):
    voice = EDGE_VOICES.get(voice_key, "en-US-AriaNeural")
    clean_text = re.sub(r'\[.*?\]', '', text).strip()
    for attempt in range(5):
        tmp_path = BASE_DIR / f"_tmp_edge_uc_{time.time_ns()}.mp3"
        async def _run():
            communicate = edge_tts.Communicate(clean_text, voice, rate="+0%", pitch="+0Hz")
            await communicate.save(str(tmp_path))
        try:
            asyncio.run(_run())
            if tmp_path.exists() and tmp_path.stat().st_size > 1000:
                data, sr = sf.read(str(tmp_path))
                tmp_path.unlink(missing_ok=True)
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                if sr != sample_rate:
                    num_samples = int(len(data) * sample_rate / sr)
                    data = signal.resample(data, num_samples)
                return data.astype(np.float32)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            time.sleep(1.5)
    return None

# Audio Processing: Future Human Daily clean_turn & Studio Room Tone
def clean_turn(x, sr=24000, gap_ms=60, max_artifact_ms=250, flat_thresh=0.3):
    x = np.asarray(x)
    if x.dtype == np.int16:
        x = x.astype(np.float32) / 32768.0
    x = x.astype(np.float32) - x.mean()

    hp = sosfilt(butter(4, 80, 'hp', fs=sr, output='sos'), x)
    fl = int(0.010 * sr)
    n = len(hp) // fl
    if n == 0: return x
    fr = hp[:n * fl].reshape(n, fl)

    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    active = db > (np.percentile(db, 95) - 35)

    spec = np.abs(np.fft.rfft(fr * np.hanning(fl), axis=1)) + 1e-9
    flat = np.exp(np.log(spec).mean(1)) / spec.mean(1)

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

    while len(runs) > 1:
        a, b = runs[-1]
        if (b - a) * 10 < max_artifact_ms and flat[a:b].mean() > flat_thresh:
            runs.pop()
        else:
            break

    start = max(0, runs[0][0] * fl - int(0.03 * sr))
    end = min(len(x), runs[-1][1] * fl + int(0.06 * sr))
    y = x[start:end].copy()

    fi, fo = int(0.008 * sr), int(0.05 * sr)
    if len(y) > fi + fo:
        y[:fi] *= np.linspace(0, 1, fi)
        y[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    return y

def apply_julian_warmth_eq(audio_samples, sample_rate=24000):
    b_highcut, a_highcut = signal.butter(2, 7500 / (sample_rate / 2), btype='low')
    audio_samples = signal.filtfilt(b_highcut, a_highcut, audio_samples)

    f0 = 150.0
    Q = 1.0
    gain_db = 4.0
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / sample_rate
    alpha = np.sin(w0) / (2 * Q)
    
    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A

    b = np.array([b0, b1, b2]) / a0
    a = np.array([a0, a1, a2]) / a0
    return signal.filtfilt(b, a, audio_samples)

def synthesize_turn_with_cache(cache_key, voice_name, text):
    cache_file = CACHE_DIR / f"{cache_key}.npy"
    if cache_file.exists():
        print(f" -> [{voice_name}] Loaded from cache!", flush=True)
        return np.load(str(cache_file))

    for model_name in TTS_MODELS:
        for attempt in range(2):
            try:
                print(f" -> Synthesizing [{voice_name}] via {model_name}...", flush=True)
                resp = client.models.generate_content(
                    model=model_name,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
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
                    return raw_samples
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print(f"    [{model_name}] Rate limited. Waiting 15s...", flush=True)
                    time.sleep(15)
                else:
                    time.sleep(2)

    # Edge-TTS Fallback
    print(f" -> [Edge-TTS Fallback] Synthesizing [{voice_name}]...", flush=True)
    edge_samples = synth_edge_turn(text, voice_name)
    if edge_samples is not None:
        np.save(str(cache_file), edge_samples)
        return edge_samples

    return None

def update_unwritten_code_rss(date_tag, date_str, ep_title, ep_summary, mp3_filename, duration_str, file_size_bytes):
    rss_file = BASE_DIR / "unwritten_code_rss.xml"
    if not rss_file.exists():
        print("[RSS ERROR] unwritten_code_rss.xml not found!", flush=True)
        return False

    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    guid = f"unwritten-code-{date_tag}"

    clean_title = ep_title.replace('&', '&amp;') if '&amp;' not in ep_title else ep_title
    clean_summary = ep_summary.replace('&', '&amp;') if '&amp;' not in ep_summary else ep_summary

    new_item = f"""    <!-- THE UNWRITTEN CODE: {date_tag} -->
    <item>
      <title>{clean_title}</title>
      <itunes:title>{clean_title}</itunes:title>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:author>Maya Lin &amp; Julian Cross</itunes:author>
      <itunes:summary>{clean_summary}</itunes:summary>
      <description><![CDATA[
        <p><strong>{clean_title}</strong></p>
        <p>{ep_summary}</p>
      ]]></description>
      <enclosure url="https://vipvan-ai.github.io/podcasts/audio/{mp3_filename}" length="{file_size_bytes}" type="audio/mpeg" />
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>no</itunes:explicit>
    </item>
"""

    marker_date = f"<!-- THE UNWRITTEN CODE: {date_tag} -->"
    if marker_date in content:
        # Replace existing episode item for today if re-running
        start_idx = content.find(marker_date)
        end_tag = "</item>"
        end_idx = content.find(end_tag, start_idx) + len(end_tag)
        updated_content = content[:start_idx] + new_item.strip() + content[end_idx:]
    else:
        atom_marker = '<atom:link href="https://vipvan-ai.github.io/podcasts/unwritten_code_rss.xml" rel="self" type="application/rss+xml" />'
        if atom_marker in content:
            insert_idx = content.find(atom_marker) + len(atom_marker)
            updated_content = content[:insert_idx] + "\n\n" + new_item.strip() + "\n" + content[insert_idx:]
        else:
            insert_idx = content.find("</channel>")
            updated_content = content[:insert_idx] + new_item + content[insert_idx:]

    rss_file.write_text(updated_content, encoding="utf-8")
    print(f"[RSS SUCCESS] Updated unwritten_code_rss.xml for {date_str}!", flush=True)
    return True

def auto_publish_to_github(commit_message):
    try:
        print("[GIT PUBLISH] Staging updated RSS feed and audio...", flush=True)
        subprocess.run(["git", "add", "unwritten_code_rss.xml", "app.js", "audio/"], cwd=str(BASE_DIR), check=True)
        print(f"[GIT PUBLISH] Committing: {commit_message}", flush=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=str(BASE_DIR), check=False)
        print("[GIT PUBLISH] Pushing to origin master...", flush=True)
        res = subprocess.run(["git", "push", "origin", "master"], cwd=str(BASE_DIR), capture_output=True, text=True)
        if res.returncode == 0:
            print("[GIT PUBLISH SUCCESS] Episode published to GitHub Pages & Spotify RSS!", flush=True)
            return True
        else:
            print(f"[GIT PUBLISH WARNING] Push output: {res.stderr}", flush=True)
            return False
    except Exception as e:
        print(f"[GIT PUBLISH ERROR] Failed to auto-publish: {e}", flush=True)
        return False

# =============================================================================
# EPISODE SCRIPTS DATABASE BY DAY OF WEEK (Imported from unwritten_code_scripts)
# =============================================================================
from unwritten_code_scripts import get_script_for_day


def run_daily_pipeline():
    # Detect current day of week (Monday=0 ... Sunday=6)
    now = datetime.now()
    day_idx = now.weekday()
    date_str = now.strftime("%B %d, %Y")
    date_tag = now.strftime("%Y%m%d")

    ep_num, ep_title, ep_summary, script_turns = get_script_for_day(day_idx)

    print("==========================================================", flush=True)
    print(f"RUNNING DAILY PODCAST GENERATOR: THE UNWRITTEN CODE", flush=True)
    print(f"Date: {date_str} (Day {day_idx}) | Episode: {ep_num}", flush=True)
    print(f"Title: {ep_title}", flush=True)
    print(f"Total Turns: {len(script_turns)}", flush=True)
    print("==========================================================", flush=True)

    sample_rate = 24000
    out_mp3_name = f"unwritten_code_{date_tag}.mp3"
    out_wav_name = f"unwritten_code_{date_tag}.wav"
    out_mp3 = AUDIO_DIR / out_mp3_name
    out_wav = AUDIO_DIR / out_wav_name

    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.32), dtype=np.float32)

    for idx, turn in enumerate(script_turns):
        cache_key = f"unwritten_code_{date_tag}_turn_{idx+1}_{turn['speaker']}"
        raw_samples = synthesize_turn_with_cache(cache_key, turn["voice"], turn["text"])
        if raw_samples is None:
            print(f"[Error] Failed to synthesize turn {idx+1}!")
            return False

        # Apply clean_turn (SFM static removal)
        cleaned = clean_turn(raw_samples, sample_rate)

        # Julian proximity warmth
        if turn["speaker"] == "Julian":
            cleaned = apply_julian_warmth_eq(cleaned, sample_rate)

        audio_chunks.append(cleaned)
        if idx < len(script_turns) - 1:
            audio_chunks.append(pause_gap)

        time.sleep(3)

    speech_track = np.concatenate(audio_chunks)

    # Continuous Room Tone Bed (-52 dBFS)
    total_len = len(speech_track)
    np.random.seed(42)
    room_noise = np.random.normal(0, 1.0, total_len).astype(np.float32)
    b_room, a_room = signal.butter(2, [120 / (sample_rate / 2), 3500 / (sample_rate / 2)], btype='band')
    filtered_room = signal.filtfilt(b_room, a_room, room_noise)
    room_target_amp = 10 ** (-52.0 / 20.0)
    filtered_room = filtered_room * (room_target_amp / (np.max(np.abs(filtered_room)) + 1e-9))

    full_audio = speech_track + filtered_room

    # Peak normalize to -1.0 dBFS
    max_peak = np.max(np.abs(full_audio))
    if max_peak > 0:
        full_audio = full_audio * (0.89125 / max_peak)

    sf.write(str(out_wav), full_audio, sample_rate)
    sf.write(str(out_mp3), full_audio, sample_rate)

    duration_sec = len(full_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes:02d}:{seconds:02d}"

    print(f"\n[MASTER COMPLETE] Audio rendered: {out_mp3}", flush=True)
    print(f"Duration: {duration_str} ({duration_sec:.2f}s)", flush=True)

    # 1. Update RSS Feed
    file_size = out_mp3.stat().st_size
    update_unwritten_code_rss(date_tag, date_str, ep_title, ep_summary, out_mp3_name, duration_str, file_size)

    # 2. Push to GitHub Pages & Spotify RSS
    auto_publish_to_github(f"Auto-publish {ep_title} ({date_str})")

    print("\n==========================================================", flush=True)
    print(f"[COMPLETE] The Unwritten Code for {date_str} published successfully!", flush=True)
    print("==========================================================", flush=True)
    return True

if __name__ == "__main__":
    run_daily_pipeline()
