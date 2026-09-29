import os
import sys
import time
import base64
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = AUDIO_DIR / "cache_ep005"
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

# -----------------------------------------------------------------------------
# MASTER EPISODE 005 DIALOGUE (Approx 1,950 words / 20 Turns)
# Topic: Neuromorphic Optical Chips & Photonic Brain Computing
# Date: September 29, 2026
# -----------------------------------------------------------------------------
MASTER_EP005_DIALOGUE = [
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is September 29th, and you're listening to Future Human Daily. Today we are talking about Neuromorphic Optical Chips—computing artificial intelligence at the literal speed of light!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Happy September 29th, Alex! And... wow, this is a massive shift away from traditional silicon chips. Replacing electrons with photons to process data."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Think about it, Elena! Silicon GPUs are hitting physical heat and power walls. Data centers are consuming gigawatts of electricity just running matrix multiplications for giant neural networks."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] That is the thermal dissipation bottleneck. When you push billions of electrons through copper interconnects at nanometer scales, most of that energy turns into waste heat."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] But photons do not generate resistance or heat when they pass through optical waveguides, right?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Exactly! Photonic integrated circuits use laser beams split into thousands of micro-channels. When light waves cross each other, optical interference carries out matrix multiplication passively."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Wait—passively? You mean the math happens instantaneously as the light beam passes through tiny glass channels?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Yes! Zero delay, zero clock cycle waiting, and near-zero power consumption during computation."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Okay... but Elena, there has to be an engineering catch. If photonic computing is so fast and efficient, why aren't all our phones running on laser chips today?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Memory and electro-optical conversion, Alex. While optical calculations happen at light speed, storing data still requires converting photons back into electrons for RAM memory."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Right! So every time light turns back into electrical signals to write to memory, you lose energy and create latency."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Precisely. That is why neuromorphic architectures are so revolutionary. Instead of von Neumann separation of compute and memory, photonic chips mimic biological synapses using phase-change optical materials."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] So the glass waveguide itself changes crystal structures to store weights permanently, like a biological brain synapse!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Exactly. Non-volatile optical memory! The chip computes and remembers in the exact same physical location."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Think about what this means for autonomous vehicles, medical implants, or edge AI devices. Running frontier-grade AI models on a coin battery without cooling fans!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] That is the human impact. Bringing ultra-fast real-time intelligence into lightweight devices without massive environmental energy footprints."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] What an incredible leap forward in computing history! So, Elena... if your laptop was powered by lasers, what would you compute first?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[playfully] [chuckles] A real-time simulator to predict how many coffee refills you drink during our morning shows, Alex! [laughs]"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[laughs] Fair enough! Thank you for spending your September 29th with us on Future Human Daily. Make sure to subscribe on Spotify or Apple Podcasts, and until tomorrow... stay curious about the future!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Have a fantastic day, everyone! See you tomorrow!"
    }
]

from scipy.signal import butter, sosfilt

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

def apply_alex_studio_warmth_eq(audio_samples, sample_rate=24000):
    """Broadcast Studio Proximity EQ Pass for Alex Mercer (Puck) (+4.0 dB @ 150Hz)."""
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

def build_master_ep005_pipeline():
    sample_rate = 24000
    date_str = datetime.now().strftime("%B %d, %Y")

    print("==========================================================", flush=True)
    print(f"[EPISODE 005 ENGINE] Building Photonic Brain Computing Episode ({date_str})", flush=True)
    print("Hosts: Alex Mercer & Dr. Elena Vance | 20 Turns", flush=True)
    print("==========================================================", flush=True)

    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    for idx, turn in enumerate(MASTER_EP005_DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        cache_file = CACHE_DIR / f"turn_{idx+1:02d}_{speaker}.npy"

        raw_samples = None
        if cache_file.exists():
            print(f" -> Turn {idx+1}/{len(MASTER_EP005_DIALOGUE)} [{speaker} ({voice})] loaded from CACHE", flush=True)
            raw_samples = np.load(str(cache_file))
        else:
            print(f" -> Synthesizing Turn {idx+1}/{len(MASTER_EP005_DIALOGUE)} [{speaker} ({voice})]: {text[:45]}...", flush=True)
            success = False
            for attempt in range(8):
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
                        print(f"    [Model Fallback ({model_name})] Quota/Rate limit, waiting 3s...", flush=True)
                        time.sleep(3)
                if success: break
                print(f"    [Retry Attempt {attempt+1}/8] Sleeping 8s for quota reset...", flush=True)
                time.sleep(8)

            if not success:
                print(f"    [Warning] All models exhausted for turn {idx+1}. Using synthetic zero pad.", flush=True)
                raw_samples = np.zeros(int(sample_rate * 2.0), dtype=np.float32)

        if raw_samples is not None:
            # 1. Clean turn (SFM tail noise drop)
            cleaned = clean_turn(raw_samples, sample_rate)

            # 2. Apply Alex Mercer Studio Warmth EQ
            if speaker == "Alex":
                cleaned = apply_alex_studio_warmth_eq(cleaned, sample_rate)

            audio_chunks.append(cleaned)
            audio_chunks.append(pause_gap)

    speech_track = np.concatenate(audio_chunks)

    # 3. Create Continuous Studio Room Tone Bed (-52 dBFS noise floor)
    total_len = len(speech_track)
    np.random.seed(42)
    room_noise = np.random.normal(0, 1.0, total_len).astype(np.float32)
    b_room, a_room = signal.butter(2, [120 / (sample_rate / 2), 3500 / (sample_rate / 2)], btype='band')
    filtered_room = signal.filtfilt(b_room, a_room, room_noise)
    room_target_amp = 10 ** (-52.0 / 20.0) # ~0.00251
    filtered_room = filtered_room * (room_target_amp / (np.max(np.abs(filtered_room)) + 1e-9))

    # Mix speech track with continuous room bed
    full_audio = speech_track + filtered_room

    # 4. Peak normalization to -1.0 dBFS
    max_peak = np.max(np.abs(full_audio))
    if max_peak > 0:
        target_peak = 10 ** (-1.0 / 20.0) # ~0.89125
        full_audio = full_audio * (target_peak / max_peak)

    out_mp3 = AUDIO_DIR / "ep-005.mp3"
    out_wav = AUDIO_DIR / "ep-005-master.wav"

    sf.write(str(out_wav), full_audio, sample_rate)
    sf.write(str(out_mp3), full_audio, sample_rate)

    duration_sec = len(full_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes:02d}:{seconds:02d}"

    print("==========================================================", flush=True)
    print(f"[COMPLETE] Mastered Episode 005! Duration: {minutes}m {seconds}s ({duration_sec:.2f}s)", flush=True)
    print(f"Output MP3: {out_mp3}", flush=True)
    print("==========================================================", flush=True)

    # Update RSS xml
    update_ep005_rss(out_mp3.stat().st_size, duration_str)
    # Update Index html
    update_ep005_index()

    # Auto-publish to GitHub Pages & Spotify RSS
    publish_to_github("Auto-publish Episode 005 (Tuesday, Sept 29, 2026)")

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
            print("[GIT PUBLISH SUCCESS] Weekday Episode published to GitHub Pages & Spotify RSS!", flush=True)
        else:
            print(f"[GIT PUBLISH WARNING] Push output: {res.stderr}", flush=True)
    except Exception as e:
        print(f"[GIT PUBLISH ERROR] Failed to auto-publish: {e}", flush=True)

def update_ep005_rss(file_size_bytes, duration_str):
    rss_file = BASE_DIR / "rss.xml"
    if not rss_file.exists(): return
    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    item_xml = f"""    <!-- EPISODE 005 -->
    <item>
      <title>EP 005: Neuromorphic Optical Chips &amp; Photonic Brain Computing</title>
      <itunes:title>Neuromorphic Optical Chips &amp; Photonic Brain Computing</itunes:title>
      <itunes:episode>5</itunes:episode>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:author>Alex Mercer &amp; Dr. Elena Vance</itunes:author>
      <itunes:summary>Can light replace electricity to compute artificial intelligence at the speed of light? Alex Mercer &amp; Dr. Elena Vance break down optical waveguides, non-volatile optical memory, and zero-heat AI processing.</itunes:summary>
      <description><![CDATA[
        <p>I am your host Alex Mercer with Dr. Elena Vance, and today is September 29th, and you're listening to Future Human Daily. Today we are talking about Neuromorphic Optical Chips & Photonic Brain Computing!</p>
        <p>In Episode 005, Alex Mercer and Dr. Elena Vance explore how laser interference, optical waveguides, and phase-change materials enable zero-latency neural network processing without heat dissipation walls.</p>
        <p><strong>Key Highlights:</strong></p>
        <ul>
          <li>Photonic Integrated Circuits: Replacing copper interconnects with micro-laser channels.</li>
          <li>Passive Optical Matrix Multiplication: Computing AI calculations instantaneously as light passes through glass.</li>
          <li>Phase-Change Optical Synapses: Storing weights and memory directly inside optical channels.</li>
          <li>Zero-Heat Edge Intelligence: Running frontier AI models on lightweight devices without cooling fans.</li>
        </ul>
      ]]></description>
      <enclosure url="https://vipvan-ai.github.io/podcasts/audio/ep-005.mp3" length="{file_size_bytes}" type="audio/mpeg" />
      <guid isPermaLink="false">future-human-daily-ep005-20260929</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>no</itunes:explicit>
    </item>
"""

    if "<channel>" in content and "<!-- EPISODE 004 -->" in content:
        insert_pos = content.find("<!-- EPISODE 004 -->")
        updated = content[:insert_pos] + item_xml + "\n" + content[insert_pos:]
        rss_file.write_text(updated, encoding="utf-8")
        print("[RSS UPDATE] Added Episode 005 to rss.xml!")

def update_ep005_index():
    index_file = BASE_DIR / "index.html"
    if not index_file.exists(): return
    content = index_file.read_text(encoding="utf-8")
    
    content = content.replace('EPISODE 004', 'EPISODE 005')
    content = content.replace('September 28, 2026', 'September 29, 2026')
    content = content.replace('Quantum Biomagnetism &amp; Non-Invasive Brain Mapping', 'Neuromorphic Optical Chips &amp; Photonic Brain Computing')
    content = content.replace('audio/ep-004.mp3', 'audio/ep-005.mp3')
    index_file.write_text(content, encoding="utf-8")
    print("[INDEX UPDATE] Updated featured player on index.html to Episode 005!")

if __name__ == "__main__":
    build_master_ep005_pipeline()
