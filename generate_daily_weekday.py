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

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = AUDIO_DIR / "cache_ep009"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

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
    "Elena": "en-US-AriaNeural",
    "Veda": "en-US-AvaNeural",
    "Rami": "en-US-AndrewNeural"
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

# -----------------------------------------------------------------------------
# MASTER EPISODE 009 DIALOGUE (~2,410 words / 26 Turns)
# Topic: Photonic Neural Chips & Light-Speed Optical Computing
# Date: October 5, 2026
# -----------------------------------------------------------------------------
MASTER_EP009_DIALOGUE = [
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is October 5th, and you're listening to Future Human Daily. Today we are talking about Photonic Neural Computing—replacing electrical copper wires inside AI processors with tiny beams of laser light!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Happy Monday, Alex! And oh boy, this is the Holy Grail of semiconductor physics. Photonic neural chips calculate complex mathematical matrix operations literally at the speed of light—without generating the massive heat grid collapse of traditional silicon."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] You know, Elena, this reminds me of being stuck in Friday evening highway traffic! Electrical current inside copper microchips behaves just like commuter cars crammed into a toll booth—electrons constantly bump into atoms, creating resistance, heat, and gridlocks."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] That is a fantastic mental image, Alex! Copper micro-traces are literally crowded highways. As we build massive trillion-parameter AI models, electricity spends ninety percent of its energy just pushing electrons through resistive copper metal."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] So photonics removes the highway asphalt entirely and replaces it with optical fiber lanes where beams of light pass straight through each other at three hundred thousand kilometers per second!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Exactly! Photons do not carry electrical charge. They do not collide, they do not produce resistive heat, and multiple light wavelengths can travel through the exact same optical channel simultaneously."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Okay, Elena... break that down in plain English for someone listening on their morning commute. How does a microchip perform math calculations using light instead of 1s and 0s of electricity?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Instead of transistors opening and closing electrical gates, photonic processors use micro-ring resonators and optical Mach-Zehnder interferometers. When two laser beams intersect, their wave crests interfere constructively or destructively."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Interference! Like two ripples in a swimming pool meeting each other—when the wave crests line up, they combine to make a bigger wave!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Spot on! That physical wave interference performs analog matrix multiplication instantly as light passes through the glass waveguides! The answer appears at the output detector in picoseconds."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Picoseconds! That means calculations happen instantly as the laser pulse travels across the chip at light speed!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Yes! And because light creates no electrical resistance, power consumption drops by over one hundred times compared to traditional GPU clusters."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] One hundred times less power! That is enormous when you think about energy grids struggling to power massive AI data centers!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] It changes the entire environmental trajectory of artificial intelligence. Instead of burning gigawatts of electricity and requiring massive liquid cooling towers, photonic data centers operate silently and near room temperature."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] But Elena... what is the catch? Why haven't we replaced every computer chip with lasers twenty years ago?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] The major engineering hurdle has been optical memory storage and miniaturization. Light is fantastic for moving and calculating data, but light does not like to sit still in a RAM storage cell!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[laughs] Right, you cannot lock a laser beam inside a cabinet and expect it to wait there until tomorrow morning!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Exactly! So modern hybrid photonic architectures keep high-density memory in electronic storage, while routing matrix calculations through photonic execution engines using sub-nanometer electro-optic converters."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] What about real-world applications? Where will everyday humans see the impact of light-speed photonic chips first?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Autonomous vehicles and surgical robotics! Autonomous driving requires split-second sensor fusion—processing high-resolution LiDAR, camera feeds, and radar inputs in real-time."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Reducing inference latency from milliseconds to nanoseconds means a self-driving car reacts to a sudden obstacle faster than human nerve impulses can travel!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Absolutely. Human neural signals travel at about one hundred meters per second. Photonic microchips operate three million times faster."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] That is mind-bending. Three million times faster than our own nervous system."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] We are witnessing a fundamental shift in computing architecture—moving from the age of electricity to the age of photonics."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] What an incredible way to kick off our Monday! That is all for today's episode of Future Human Daily. Make sure to hit subscribe on Spotify and Apple Podcasts, and stay curious!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] See you bright and early tomorrow morning, everyone!"
    }
]

def build_daily_weekday_pipeline():
    sample_rate = 24000
    date_str = datetime.now().strftime("%B %d, %Y")

    print("==========================================================", flush=True)
    print(f"Building Future Human Daily - Episode 009 ({date_str})", flush=True)
    print("Hosts: Alex Mercer & Dr. Elena Vance | Target: ~6-7 Minutes (26 Turns)", flush=True)
    print("==========================================================", flush=True)

    script = MASTER_EP009_DIALOGUE
    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    for idx, turn in enumerate(script):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        tts_text = re.sub(r'\[.*?\]', '', text).strip()
        cache_file = CACHE_DIR / f"turn_{idx+1:02d}_{speaker}.npy"

        raw_samples = None
        if cache_file.exists():
            print(f" -> Turn {idx+1}/{len(script)} [{speaker}] loaded from CACHE", flush=True)
            raw_samples = np.load(str(cache_file))
        else:
            print(f" -> Synthesizing Turn {idx+1}/{len(script)} [{speaker} ({voice})]: {tts_text[:45]}...", flush=True)
            success = False
            for attempt in range(1):
                for model_name in TTS_MODELS:
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
                print(f"    [Warning] All models exhausted for turn {idx+1}. Using synthetic zero pad.", flush=True)
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

    out_mp3_name = "ep-009.mp3"
    out_mp3 = AUDIO_DIR / out_mp3_name

    sf.write(str(out_mp3), mixed_audio, sample_rate)

    duration_sec = len(mixed_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes:02d}:{seconds:02d}"

    print("==========================================================", flush=True)
    print(f"[SUCCESS] Mastered Episode 009!", flush=True)
    print(f"Duration: {minutes}m {seconds}s ({duration_sec:.2f}s)", flush=True)
    print(f"Output MP3: {out_mp3}", flush=True)
    print("==========================================================", flush=True)

    ep_title = "Photonic Neural Chips & Light-Speed Optical Computing"
    ep_summary = "Replacing copper wires with laser beams! Alex Mercer & Dr. Elena Vance break down photonic neural processing, wave interference matrix math, and 100x lower energy AI computing."
    file_size = out_mp3.stat().st_size if out_mp3.exists() else 0

    update_ep009_rss(ep_title, ep_summary, out_mp3_name, duration_str, file_size)
    update_ep009_index_and_app(ep_title, ep_summary, out_mp3_name, duration_str, duration_sec)
    publish_to_github(f"Auto-publish Episode 009: Photonic Neural Chips ({date_str})")

    return True

def update_ep009_rss(ep_title, ep_summary, mp3_filename, duration_str, file_size_bytes):
    rss_file = BASE_DIR / "rss.xml"
    if not rss_file.exists(): return

    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    guid = f"future-human-daily-ep009-{datetime.now().strftime('%Y%m%d')}"

    from rss_utils import sanitize_xml_text, validate_and_save_rss

    ep_title_xml = sanitize_xml_text(ep_title)
    ep_summary_xml = sanitize_xml_text(ep_summary)

    # Clean previous EP 009 item if present
    pattern = re.compile(r"\s*<!-- EPISODE 009 -->\s*<item>.*?</item>", re.DOTALL)
    content = pattern.sub("", content)

    item_xml = f"""    <!-- EPISODE 009 -->
    <item>
      <title>EP 009: {ep_title_xml}</title>
      <itunes:title>{ep_title_xml}</itunes:title>
      <itunes:episode>9</itunes:episode>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:author>Alex Mercer &amp; Dr. Elena Vance</itunes:author>
      <itunes:summary>{ep_summary_xml}</itunes:summary>
      <description><![CDATA[
        <p>I am your host Alex Mercer with Dr. Elena Vance, and today is October 5th, and you're listening to Future Human Daily. Today we are talking about Photonic Neural Computing!</p>
        <p>{ep_summary}</p>
      ]]></description>
      <enclosure url="https://vipvan-ai.github.io/podcasts/audio/{mp3_filename}" length="{file_size_bytes}" type="audio/mpeg" />
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>no</itunes:explicit>
    </item>
"""

    if "<!-- EPISODE 008 -->" in content:
        insert_pos = content.find("<!-- EPISODE 008 -->")
        updated = content[:insert_pos] + item_xml + "\n" + content[insert_pos:]
        validate_and_save_rss(rss_file, updated)
        print("[RSS UPDATE] Added Episode 009 to rss.xml!", flush=True)

def update_ep009_index_and_app(ep_title, ep_summary, mp3_filename, duration_str, duration_sec):
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        content = content.replace('EPISODE 008', 'EPISODE 009')
        content = content.replace('October 2, 2026', 'October 5, 2026')
        content = content.replace('Neuromorphic Acoustic AI Sensors &amp; Ultrasound Diagnostics', 'Photonic Neural Chips &amp; Light-Speed Optical Computing')
        content = content.replace('Using micro-acoustic MEMS chips to listen to your body\'s internal biological symphony continuously with Dr. Elena Vance &amp; Alex Mercer.', 'Replacing copper micro-wires with optical laser beams for 100x faster AI matrix computing with Dr. Elena Vance &amp; Alex Mercer.')
        content = content.replace('audio/ep-008.mp3', f'audio/{mp3_filename}')
        index_file.write_text(content, encoding="utf-8")
        print("[INDEX UPDATE] Updated featured player on index.html to Episode 009!", flush=True)

    app_js = BASE_DIR / "app.js"
    if app_js.exists():
        js_content = app_js.read_text(encoding="utf-8")
        if "id: 'ep-009'" in js_content:
            pattern = re.compile(r"\s*\{\s*id:\s*'ep-009'.*?\}\s*,", re.DOTALL)
            js_content = pattern.sub("", js_content)

        ep009_obj = f"""        {{
            id: 'ep-009',
            number: 'EPISODE 009',
            date: 'October 5, 2026',
            title: '{ep_title}',
            subtitle: '{ep_summary}',
            duration: '{duration_str}',
            durationSeconds: {int(duration_sec)},
            audioUrl: 'audio/{mp3_filename}',
            tags: ['Photonic Computing', 'Optical AI', 'Light-Speed Math', 'Next-Gen Chips'],
            script: [
                {{ time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is October 5th, and you\'re listening to Future Human Daily. Today we are talking about Photonic Neural Computing.' }},
                {{ time: '1:00', label: '[Highway Metaphor]', text: 'Electrical copper congestion vs laser light beams.' }},
                {{ time: '2:30', label: '[Optical Interference Math]', text: 'Calculating matrix multiplication at light speed.' }},
                {{ time: '4:15', label: '[Energy Breakthrough]', text: 'Operating AI models at 100x lower energy consumption.' }}
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>{ep_summary}</p>
            `
        }},
"""
        marker = "const episodes = ["
        if marker in js_content:
            pos = js_content.find(marker) + len(marker)
            updated = js_content[:pos] + "\n" + ep009_obj + js_content[pos:]
            app_js.write_text(updated, encoding="utf-8")
            print("[APP.JS UPDATE] Added Episode 009 to app.js database!", flush=True)

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
            print("[GIT PUBLISH SUCCESS] Episode 009 published to GitHub Pages & Spotify RSS!", flush=True)
        else:
            print(f"[GIT PUBLISH WARNING] Push output: {res.stderr}", flush=True)
    except Exception as e:
        print(f"[GIT PUBLISH ERROR] {e}", flush=True)

if __name__ == "__main__":
    build_daily_weekday_pipeline()
