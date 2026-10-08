import os
import sys
import time
import base64
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

from future_human_weekday_scripts import get_future_human_script_for_day
from rss_utils import sanitize_xml_text, validate_and_save_rss

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

EDGE_VOICES = {
    "Alex": "en-US-GuyNeural",
    "Elena": "en-US-AriaNeural"
}

def synth_edge_turn(text, speaker, sample_rate=24000):
    voice = EDGE_VOICES.get(speaker, "en-US-GuyNeural")
    for attempt in range(5):
        tmp_path = Path(f"_tmp_edge_{time.time_ns()}.mp3")
        async def _run():
            communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
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

def apply_studio_warmth_eq(audio_samples, sample_rate=24000, low_boost_db=4.0):
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

def build_daily_weekday_pipeline():
    now = datetime.now()
    day_idx = now.weekday()
    date_str = now.strftime("%B %d, %Y")
    date_tag = now.strftime("%Y%m%d")

    title, summary, script_turns = get_future_human_script_for_day(day_idx, date_str)
    out_mp3_name = f"future_human_{date_tag}.mp3"
    out_mp3 = AUDIO_DIR / out_mp3_name
    cache_dir = AUDIO_DIR / f"cache_fhd_{date_tag}"
    cache_dir.mkdir(parents=True, exist_ok=True)

    sample_rate = 24000
    print("==========================================================", flush=True)
    print(f"BUILDING FUTURE HUMAN DAILY: {title} ({date_str})", flush=True)
    print(f"Total Turns: {len(script_turns)}", flush=True)
    print("==========================================================", flush=True)

    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    for idx, turn in enumerate(script_turns):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        tts_text = re.sub(r'\[.*?\]', '', text).strip()
        cache_file = cache_dir / f"turn_{idx+1:02d}_{speaker}.npy"

        raw_samples = None
        if cache_file.exists():
            print(f" -> Turn {idx+1}/{len(script_turns)} [{speaker}] loaded from CACHE", flush=True)
            raw_samples = np.load(str(cache_file))
        else:
            print(f" -> Synthesizing Turn {idx+1}/{len(script_turns)} [{speaker}]: {tts_text[:40]}...", flush=True)
            success = False
            for model_name in TTS_MODELS:
                for retry in range(2):
                    try:
                        resp = client.models.generate_content(
                            model=model_name,
                            contents=tts_text,
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
                            print(f"    [Success (Gemini {model_name})] Cached {len(raw_samples)} samples.", flush=True)
                            success = True
                            time.sleep(1)
                            break
                    except Exception:
                        pass
                if success:
                    break

            if not success:
                print(f"    [Fallback Edge-TTS] Synthesizing {speaker} with Edge-TTS HD Voice...", flush=True)
                raw_samples = synth_edge_turn(tts_text, speaker, sample_rate)
                if raw_samples is not None:
                    np.save(str(cache_file), raw_samples)
                    print(f"    [Success (Edge-TTS)] Cached {len(raw_samples)} samples.", flush=True)
                    success = True

            if not success:
                print(f"    [Warning] All models exhausted for turn {idx+1}. Using synthetic pad.", flush=True)
                raw_samples = np.zeros(int(sample_rate * 2.0), dtype=np.float32)

        if raw_samples is not None:
            cleaned = clean_turn(raw_samples, sample_rate)
            warmed = apply_studio_warmth_eq(cleaned, sample_rate)
            audio_chunks.append(warmed)
            audio_chunks.append(pause_gap)

    if not audio_chunks:
        print("[Error] No audio chunks synthesized!")
        return False

    speech_track = np.concatenate(audio_chunks)
    total_len = len(speech_track)
    np.random.seed(42)
    room_noise = np.random.normal(0, 1.0, total_len).astype(np.float32)
    b_room, a_room = signal.butter(2, [120 / (sample_rate / 2), 3500 / (sample_rate / 2)], btype='band')
    filtered_room = signal.filtfilt(b_room, a_room, room_noise)
    room_target_amp = 10 ** (-52.0 / 20.0)
    filtered_room = filtered_room * (room_target_amp / (np.max(np.abs(filtered_room)) + 1e-9))

    mixed_audio = speech_track + filtered_room
    max_peak = np.max(np.abs(mixed_audio))
    if max_peak > 0:
        target_peak = 10 ** (-1.0 / 20.0)
        mixed_audio = mixed_audio * (target_peak / max_peak)

    sf.write(str(out_mp3), mixed_audio, sample_rate)

    duration_sec = len(mixed_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes:02d}:{seconds:02d}"

    print("==========================================================", flush=True)
    print(f"[SUCCESS] Mastered Future Human Daily for {date_str}!", flush=True)
    print(f"Duration: {minutes}m {seconds}s ({duration_sec:.2f}s)", flush=True)
    print(f"Output MP3: {out_mp3}", flush=True)
    print("==========================================================", flush=True)

    file_size = out_mp3.stat().st_size if out_mp3.exists() else 0

    update_fhd_rss(title, summary, out_mp3_name, duration_str, file_size, date_tag)
    update_fhd_index_and_app(title, summary, out_mp3_name, duration_str, duration_sec, date_str, date_tag)
    publish_to_github(f"Auto-publish Future Human Daily: {title} ({date_str})")
    return True

def update_fhd_rss(ep_title, ep_summary, mp3_filename, duration_str, file_size_bytes, date_tag):
    rss_file = BASE_DIR / "rss.xml"
    if not rss_file.exists(): return

    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    guid = f"future-human-daily-{date_tag}"

    ep_title_xml = sanitize_xml_text(ep_title)
    ep_summary_xml = sanitize_xml_text(ep_summary)

    # Clean existing item with same guid if present
    pattern = re.compile(rf"\s*<!-- FUTURE HUMAN DAILY: {date_tag} -->\s*<item>.*?</item>", re.DOTALL)
    content = pattern.sub("", content)

    item_xml = f"""    <!-- FUTURE HUMAN DAILY: {date_tag} -->
    <item>
      <title>{ep_title_xml}</title>
      <itunes:title>{ep_title_xml}</itunes:title>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:author>Alex Mercer &amp; Dr. Elena Vance</itunes:author>
      <itunes:summary>{ep_summary_xml}</itunes:summary>
      <description><![CDATA[
        <p>{ep_summary}</p>
      ]]></description>
      <enclosure url="https://vipvan-ai.github.io/podcasts/audio/{mp3_filename}" length="{file_size_bytes}" type="audio/mpeg" />
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>no</itunes:explicit>
    </item>
"""

    marker = '<atom:link href="https://vipvan-ai.github.io/podcasts/rss.xml" rel="self" type="application/rss+xml" />'
    if marker in content:
        insert_pos = content.find(marker) + len(marker)
        updated = content[:insert_pos] + "\n\n" + item_xml.strip() + "\n" + content[insert_pos:]
        validate_and_save_rss(rss_file, updated)
        print(f"[RSS UPDATE] Added {ep_title} to top of rss.xml!", flush=True)

def update_fhd_index_and_app(ep_title, ep_summary, mp3_filename, duration_str, duration_sec, date_str, date_tag):
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        content = re.sub(r'<span class="ep-badge" id="ep-number">.*?</span>', f'<span class="ep-badge" id="ep-number">DAILY DEEP DIVE</span>', content)
        content = re.sub(r'<span class="ep-date" id="ep-date">.*?</span>', f'<span class="ep-date" id="ep-date">{date_str}</span>', content)
        content = re.sub(r'<h1 class="ep-title" id="ep-title">.*?</h1>', f'<h1 class="ep-title" id="ep-title">{ep_title}</h1>', content)
        content = re.sub(r'<p class="ep-subtitle" id="ep-subtitle">.*?</p>', f'<p class="ep-subtitle" id="ep-subtitle">{ep_summary}</p>', content)
        content = re.sub(r'<source src="audio/.*?"', f'<source src="audio/{mp3_filename}"', content)
        index_file.write_text(content, encoding="utf-8")
        print("[INDEX UPDATE] Updated featured player on index.html!", flush=True)

    app_js = BASE_DIR / "app.js"
    if app_js.exists():
        js_content = app_js.read_text(encoding="utf-8")
        ep_id = f"fhd-{date_tag}"
        if f"id: '{ep_id}'" in js_content:
            pattern = re.compile(rf"\s*\{{\s*id:\s*'{ep_id}'.*?\}}\s*,", re.DOTALL)
            js_content = pattern.sub("", js_content)

        clean_title_js = ep_title.replace("'", "\\'")
        clean_sub_js = ep_summary.replace("'", "\\'")

        fhd_obj = f"""        {{
            id: '{ep_id}',
            number: '{date_str.upper()}',
            date: '{date_str}',
            title: '{clean_title_js}',
            subtitle: '{clean_sub_js}',
            duration: '{duration_str}',
            durationSeconds: {int(duration_sec)},
            audioUrl: 'audio/{mp3_filename}',
            tags: ['Future Human Daily', 'Alex & Elena', 'Bio-Computing', 'Emerging Tech'],
            script: [
                {{ time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is {date_str}, and you\\\'re listening to Future Human Daily.' }}
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>{clean_sub_js}</p>
            `
        }},
"""
        marker = "const episodes = ["
        if marker in js_content:
            pos = js_content.find(marker) + len(marker)
            updated = js_content[:pos] + "\n" + fhd_obj + js_content[pos:]
            app_js.write_text(updated, encoding="utf-8")
            print(f"[APP.JS UPDATE] Added {ep_title} to app.js database!", flush=True)

def publish_to_github(commit_message):
    import subprocess
    try:
        print("[GIT PUBLISH] Staging updated RSS feed and episode audio...", flush=True)
        subprocess.run(["git", "add", "index.html", "app.js", "rss.xml", "audio/", "*.py", "*.bat"], cwd=str(BASE_DIR), check=True)
        print(f"[GIT PUBLISH] Committing: {commit_message}", flush=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=str(BASE_DIR), check=False)
        print("[GIT PUBLISH] Pushing to origin master...", flush=True)
        res = subprocess.run(["git", "push", "origin", "master"], cwd=str(BASE_DIR), capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[GIT PUBLISH SUCCESS] Published to GitHub Pages & Spotify RSS!", flush=True)
        else:
            print(f"[GIT PUBLISH WARNING] Push output: {res.stderr}", flush=True)
    except Exception as e:
        print(f"[GIT PUBLISH ERROR] {e}", flush=True)

if __name__ == "__main__":
    build_daily_weekday_pipeline()
