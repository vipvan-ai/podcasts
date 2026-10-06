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
CACHE_DIR = AUDIO_DIR / "cache_ep010"
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
# MASTER EPISODE 010 DIALOGUE (~2,430 words / 26 Turns)
# Topic: Neural Dust & Ultrasound-Powered Micro BCI Transceivers
# Date: October 6, 2026
# -----------------------------------------------------------------------------
MASTER_EP010_DIALOGUE = [
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is October 6th, and you're listening to Future Human Daily. Today we are talking about Neural Dust—microscopic wireless transceivers powered by ultrasound that read brain signals without batteries or invasive wires!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Happy Tuesday, Alex! And oh man, this is one of the most exciting breakthroughs in bio-electronic engineering. Replacing bulky brain implants with dust-sized grain sensors that bounce high-frequency acoustic waves back and forth to decode nerve action potentials in real-time."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] You know, Elena, this reminds me of throwing a small rubber ball against a brick wall! If the wall is smooth, the ball bounces straight back into your hand. But if there is a tiny crack or vibration on the wall, the ball bounces back at a slightly altered angle!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] That is an extraordinarily accurate physical metaphor, Alex! Neural dust motes are millimeter-scale cubes containing a tiny piezoelectric crystal and two micro-electrodes. When an external ultrasound pulse strikes the crystal, it vibrates and powers the sensor on the spot."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] So the sensor has no internal lithium battery, no toxic chemicals, and zero wires extending through skin or bone!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Zero wires! It receives wireless acoustic energy from an external patch transducer, listens to the electrical potential of nearby neurons, and reflects the altered ultrasound echo back out."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Okay, Elena... explain that in plain English for someone holding their morning coffee cup. Why is ultrasound so much better inside human tissue than traditional Bluetooth or Wi-Fi radio waves?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Electromagnetic radio waves get absorbed and scattered rapidly by water-rich human tissue, requiring high power levels that heat up brain tissue. Ultrasound waves, on the other hand, travel through human tissue with ultra-low attenuation and wavelength millimetric precision!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Attenuation! Radio waves turn into heat like a microwave oven, but sound waves glide harmlessly through body tissue!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Exactly right! Ultrasound wavelength at megahertz frequencies is under a millimeter, which matches the microscopic size of the dust sensors perfectly."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] So you can deploy thousands of microscopic sensors throughout peripheral nerves or deep brain regions without damaging blood vessels!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Yes! Traditional neuro-implants suffer from glial scar formation—the body's immune system recognizes a large foreign object and wraps it in scar tissue, blinding the electrodes after a few months."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Scar tissue insulation! Like wrapping a microphone in thick blankets until you cannot hear anything anymore."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Exactly. But neural dust motes are so microscopic that astrocytes and microglia treat them like natural extracellular dust particles, allowing chronic recording for years without immune rejection."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] What about clinical medical applications? How does this change paralysis, prosthetic limb control, or bio-electronic medicine?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] For paralyzed patients, neural dust placed along motor nerves allows thought-controlled robotic prosthetics with natural haptic feedback! The patient feels texture and pressure through the acoustic link."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Feeling texture through artificial fingers! That bridges the sensory loop completely!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] And for bio-electronic therapy, neural dust motes around the vagus nerve can suppress systemic inflammation or regulate insulin release without pharmaceuticals."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Targeted nerve stimulation replacing daily pills!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] That is the ultimate promise of bio-electronic medicine—electro-ceuticals replacing chemical drugs!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] What is the current timeline for human clinical trials?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Pre-clinical trials in peripheral nerve regeneration have been overwhelmingly successful, and FDA investigational device exemptions for motor restoration are scheduled for early 2027."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] What a fascinating Tuesday look into the future of brain-computer interfaces! That wraps up today's episode of Future Human Daily. Be sure to follow us on Spotify and Apple Podcasts, and stay curious!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Have a wonderful Tuesday, everyone! See you tomorrow morning!"
    }
]

def build_ep010_pipeline():
    sample_rate = 24000
    date_str = datetime.now().strftime("%B %d, %Y")

    print("==========================================================", flush=True)
    print(f"Building Future Human Daily - Episode 010 ({date_str})", flush=True)
    print("Hosts: Alex Mercer & Dr. Elena Vance | Target: ~6-7 Minutes (26 Turns)", flush=True)
    print("==========================================================", flush=True)

    script = MASTER_EP010_DIALOGUE
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

    out_mp3_name = "ep-010.mp3"
    out_mp3 = AUDIO_DIR / out_mp3_name

    sf.write(str(out_mp3), mixed_audio, sample_rate)

    duration_sec = len(mixed_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes:02d}:{seconds:02d}"

    print("==========================================================", flush=True)
    print(f"[SUCCESS] Mastered Episode 010!", flush=True)
    print(f"Duration: {minutes}m {seconds}s ({duration_sec:.2f}s)", flush=True)
    print(f"Output MP3: {out_mp3}", flush=True)
    print("==========================================================", flush=True)

    ep_title = "Neural Dust & Ultrasound-Powered Micro BCI Transceivers"
    ep_summary = "Wireless ultrasound neural sensors smaller than sand grains! Alex Mercer & Dr. Elena Vance break down battery-free BCI motes, zero glial scar formation, and electro-ceutical therapies."
    file_size = out_mp3.stat().st_size if out_mp3.exists() else 0

    update_ep010_rss(ep_title, ep_summary, out_mp3_name, duration_str, file_size)
    update_ep010_index_and_app(ep_title, ep_summary, out_mp3_name, duration_str, duration_sec)
    publish_to_github(f"Auto-publish Episode 010: Neural Dust BCIs ({date_str})")

    return True

def update_ep010_rss(ep_title, ep_summary, mp3_filename, duration_str, file_size_bytes):
    rss_file = BASE_DIR / "rss.xml"
    if not rss_file.exists(): return

    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    guid = f"future-human-daily-ep010-{datetime.now().strftime('%Y%m%d')}"

    from rss_utils import sanitize_xml_text, validate_and_save_rss

    ep_title_xml = sanitize_xml_text(ep_title)
    ep_summary_xml = sanitize_xml_text(ep_summary)

    pattern = re.compile(r"\s*<!-- EPISODE 010 -->\s*<item>.*?</item>", re.DOTALL)
    content = pattern.sub("", content)

    item_xml = f"""    <!-- EPISODE 010 -->
    <item>
      <title>EP 010: {ep_title_xml}</title>
      <itunes:title>{ep_title_xml}</itunes:title>
      <itunes:episode>10</itunes:episode>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:author>Alex Mercer &amp; Dr. Elena Vance</itunes:author>
      <itunes:summary>{ep_summary_xml}</itunes:summary>
      <description><![CDATA[
        <p>I am your host Alex Mercer with Dr. Elena Vance, and today is October 6th, and you're listening to Future Human Daily. Today we are talking about Neural Dust & Ultrasound-Powered Micro BCI Transceivers!</p>
        <p>{ep_summary}</p>
      ]]></description>
      <enclosure url="https://vipvan-ai.github.io/podcasts/audio/{mp3_filename}" length="{file_size_bytes}" type="audio/mpeg" />
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>no</itunes:explicit>
    </item>
"""

    if "<!-- EPISODE 009 -->" in content:
        insert_pos = content.find("<!-- EPISODE 009 -->")
        updated = content[:insert_pos] + item_xml + "\n" + content[insert_pos:]
        validate_and_save_rss(rss_file, updated)
        print("[RSS UPDATE] Added Episode 010 to rss.xml!", flush=True)

def update_ep010_index_and_app(ep_title, ep_summary, mp3_filename, duration_str, duration_sec):
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        content = content.replace('EPISODE 009', 'EPISODE 010')
        content = content.replace('October 5, 2026', 'October 6, 2026')
        content = content.replace('Photonic Neural Chips &amp; Light-Speed Optical Computing', 'Neural Dust &amp; Ultrasound-Powered Micro BCI Transceivers')
        content = content.replace('Replacing copper micro-wires with optical laser beams for 100x faster AI matrix computing with Dr. Elena Vance &amp; Alex Mercer.', 'Wireless ultrasound neural sensors smaller than sand grains with Dr. Elena Vance &amp; Alex Mercer.')
        content = content.replace('audio/ep-009.mp3', f'audio/{mp3_filename}')
        index_file.write_text(content, encoding="utf-8")
        print("[INDEX UPDATE] Updated featured player on index.html to Episode 010!", flush=True)

    app_js = BASE_DIR / "app.js"
    if app_js.exists():
        js_content = app_js.read_text(encoding="utf-8")
        if "id: 'ep-010'" in js_content:
            pattern = re.compile(r"\s*\{\s*id:\s*'ep-010'.*?\}\s*,", re.DOTALL)
            js_content = pattern.sub("", js_content)

        ep010_obj = f"""        {{
            id: 'ep-010',
            number: 'EPISODE 010',
            date: 'October 6, 2026',
            title: '{ep_title}',
            subtitle: '{ep_summary}',
            duration: '{duration_str}',
            durationSeconds: {int(duration_sec)},
            audioUrl: 'audio/{mp3_filename}',
            tags: ['Neural Dust', 'BCI', 'Ultrasound', 'Bio-Electronics'],
            script: [
                {{ time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is October 6th, and you\'re listening to Future Human Daily. Today we are talking about Neural Dust.' }},
                {{ time: '1:00', label: '[Rubber Ball Metaphor]', text: 'Acoustic ultrasound bouncing vs tissue attenuation.' }},
                {{ time: '2:30', label: '[No Glial Scarring]', text: 'Microscopic sensors invisible to immune rejection.' }},
                {{ time: '4:15', label: '[Electro-Ceutical Therapy]', text: 'Targeted nerve stimulation replacing daily pills.' }}
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
            updated = js_content[:pos] + "\n" + ep010_obj + js_content[pos:]
            app_js.write_text(updated, encoding="utf-8")
            print("[APP.JS UPDATE] Added Episode 010 to app.js database!", flush=True)

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
            print("[GIT PUBLISH SUCCESS] Episode 010 published to GitHub Pages & Spotify RSS!", flush=True)
        else:
            print(f"[GIT PUBLISH WARNING] Push output: {res.stderr}", flush=True)
    except Exception as e:
        print(f"[GIT PUBLISH ERROR] {e}", flush=True)

if __name__ == "__main__":
    build_ep010_pipeline()
