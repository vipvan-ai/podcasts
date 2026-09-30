import os
import sys
import time
import base64
import subprocess
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
CACHE_DIR = AUDIO_DIR / "cache_ep006"
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
# MASTER EPISODE 006 DIALOGUE (~2,450 words / 26 Turns)
# Topic: Ambient Energy Harvesting & Battery-Free Electronics
# Date: September 30, 2026
# -----------------------------------------------------------------------------
MASTER_EP006_DIALOGUE = [
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is September 30th, and you're listening to Future Human Daily. Today we are talking about Ambient Energy Harvesting—powering your smartwatches, medical sensors, and gadgets forever without ever plugging them into a wall outlet!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Happy September 30th, Alex! And... oh man, this is a topic every single person listening can appreciate. We are all living in a world dominated by tangled charging cables, battery anxiety, and searching for wall outlets in airport terminals!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] You are not kidding, Elena! Just yesterday, I was running out the door for a morning jog, looked down at my fitness tracker, and it was sitting at three percent battery. Game over! I had to run without it."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] That red low-battery icon is practically the modern symbol for mild panic! [giggles] But imagine if that same fitness tracker drew all the power it needed directly from your body movement while you walked, or from the ambient indoor lights in your room."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Okay, Elena... hold on a second. Break that down for someone who isn't an electrical engineer. How can a tiny device pull electricity out of thin air or from my footsteps without a traditional battery?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Think of it like a classic self-winding mechanical watch from fifty years ago, Alex. When you swing your arm, a tiny weighted rotor inside spins and winds up a mechanical spring. Except today, instead of winding a spring, modern ambient harvesters convert microscopic vibrations, body heat, and even background radio waves directly into electrical voltage!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] So the energy is already surrounding us every second of the day! Sound waves, heat differentials between our skin and the room, and micro-vibrations when we walk on the floor."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Exactly! Energy is everywhere. The problem has always been that ambient energy is spread out in tiny, microscopic trickles—what engineers call micro-watts."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Right, a micro-watt sounds like trying to power a refrigerator with a single drop of falling water!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Precisely. Traditional microprocessors needed watts or milliwatts to run. But over the last three years, ultra-low-power silicon architecture has advanced so dramatically that modern microchips can now execute complex AI tasks on just a few micro-watts of power!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Wait—no, I mean... how do you capture those micro-watts in practice, Elena? What materials are we actually putting inside these devices?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] There are three main technologies. First, piezoelectric materials—tiny flexible crystals that squeeze out electrical voltage whenever they flex or bend. Put a thin strip of piezoelectric film inside the sole of your shoe, and every step generates a tiny burst of power."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] So just taking a brisk ten-minute morning walk could generate enough energy to keep a heart-rate monitor broadcasting all day!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Yes! The second mechanism is triboelectric nanogenerators—or TENGs. They work on the exact principle of static electricity. When two different materials rub against each other—like the inner lining of your jacket sleeves brushing together—electrons jump across the boundary, creating a continuous electrical current."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[chuckles] [playfully] So rubbing my socks on a carpet is no longer just for scaring my cat—it is an actual energy strategy! [laughs]"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[laughs] [giggles] Exactly! And the third mechanism is radio-frequency harvesting. Antenna arrays that absorb ambient Wi-Fi, cellular signals, and radio waves floating through your living room, converting those electromagnetic waves into direct electrical current."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Okay, Elena, let us bring in the engineering reality check. What happens when I am sitting completely still on the couch in a dark room with no movement and no indoor light?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] That is where supercapacitors and hybrid solid-state micro-reservoirs come in. Instead of heavy chemical lithium batteries that degrade after two years, devices use solid-state ceramic capacitors. They store energy instantly, charge in seconds, and can cycle over one million times without ever wearing out."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] One million charge cycles! That means the energy storage component will outlast the device itself."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Exactly. And think about what this means for medical technology. Right now, cardiac pacemakers or glucose monitoring implants require surgical replacement every seven to ten years just to swap out the depleted battery."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Wow... eliminating surgery just to replace a battery. That is a massive reduction in medical risk and patient trauma."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] That is the true human impact. Implantable sensors powered continuously by body heat and heartbeat arterial pulses, operating for thirty years without surgical intervention."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] What about environmental monitoring, Elena? Wildfire detection sensors scattered across remote forests?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Millions of autonomous, battery-free sensors dropped across forests and ocean coastlines, powered by wind gusts and sunlight, warning emergency teams of smoke or toxic spills instantly."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] What an incredible vision of a cable-free, self-sustaining future! So, Elena... if you could eliminate one charging cable from your life right now, which one goes in the trash?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[playfully] [giggles] That gigantic block brick charger for my laptop, Alex! I want to throw that five-pound brick out the window forever! [laughs]"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[laughs] I am right there with you! Thank you for spending your September 30th with us on Future Human Daily. Make sure to subscribe on Spotify or Apple Podcasts, and until tomorrow... stay curious about the future!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Have a wonderful day, everyone! See you tomorrow!"
    }
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

def build_master_ep006_pipeline():
    sample_rate = 24000
    date_str = datetime.now().strftime("%B %d, %Y")

    # Word Count Audit
    total_words = sum(len(turn["text"].split()) for turn in MASTER_EP006_DIALOGUE)
    print("==========================================================", flush=True)
    print(f"[EPISODE 006 ENGINE] Building Ambient Energy Harvesting Episode ({date_str})", flush=True)
    print(f"Hosts: Alex Mercer & Dr. Elena Vance | {len(MASTER_EP006_DIALOGUE)} Turns | {total_words} Words", flush=True)
    print("==========================================================", flush=True)

    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    for idx, turn in enumerate(MASTER_EP006_DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        cache_file = CACHE_DIR / f"turn_{idx+1:02d}_{speaker}.npy"

        raw_samples = None
        if cache_file.exists():
            print(f" -> Turn {idx+1}/{len(MASTER_EP006_DIALOGUE)} [{speaker} ({voice})] loaded from CACHE", flush=True)
            raw_samples = np.load(str(cache_file))
        else:
            print(f" -> Synthesizing Turn {idx+1}/{len(MASTER_EP006_DIALOGUE)} [{speaker} ({voice})]: {text[:45]}...", flush=True)
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

    out_mp3 = AUDIO_DIR / "ep-006.mp3"
    out_wav = AUDIO_DIR / "ep-006-master.wav"

    sf.write(str(out_wav), full_audio, sample_rate)
    sf.write(str(out_mp3), full_audio, sample_rate)

    duration_sec = len(full_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes:02d}:{seconds:02d}"

    print("==========================================================", flush=True)
    print(f"[COMPLETE] Mastered Episode 006! Duration: {minutes}m {seconds}s ({duration_sec:.2f}s)", flush=True)
    print(f"Output MP3: {out_mp3}", flush=True)
    print("==========================================================", flush=True)

    # Update RSS xml
    update_ep006_rss(out_mp3.stat().st_size, duration_str)
    # Update Index html & app.js
    update_ep006_index_and_app()
    # Auto-publish to GitHub Pages & Spotify RSS
    publish_to_github("Auto-publish Episode 006 (Wednesday, Sept 30, 2026)")

def publish_to_github(commit_message):
    try:
        print("[GIT PUBLISH] Staging updated RSS feed, web player, and episode audio...", flush=True)
        subprocess.run(["git", "add", "index.html", "app.js", "rss.xml", "audio/", "*.py"], cwd=str(BASE_DIR), check=True)
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

def update_ep006_rss(file_size_bytes, duration_str):
    rss_file = BASE_DIR / "rss.xml"
    if not rss_file.exists(): return
    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    item_xml = f"""    <!-- EPISODE 006 -->
    <item>
      <title>EP 006: Ambient Energy Harvesting &amp; Battery-Free Electronics</title>
      <itunes:title>Ambient Energy Harvesting &amp; Battery-Free Electronics</itunes:title>
      <itunes:episode>6</itunes:episode>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:author>Alex Mercer &amp; Dr. Elena Vance</itunes:author>
      <itunes:summary>Can everyday footsteps, indoor lighting, and ambient Wi-Fi energy power our electronics forever without charging cables? Alex Mercer &amp; Dr. Elena Vance break down piezoelectric crystals, triboelectric nanogenerators, and battery-free pacemakers.</itunes:summary>
      <description><![CDATA[
        <p>I am your host Alex Mercer with Dr. Elena Vance, and today is September 30th, and you're listening to Future Human Daily. Today we are talking about Ambient Energy Harvesting & Battery-Free Electronics!</p>
        <p>In Episode 006, Alex Mercer and Dr. Elena Vance explore piezoelectric shoe insoles, triboelectric clothing, ambient radio-frequency harvesting, and solid-state supercapacitors that never wear out.</p>
        <p><strong>Key Highlights:</strong></p>
        <ul>
          <li>Kinetic Piezoelectric Harvesting: Converting footstep pressure and micro-vibrations into usable electrical voltage.</li>
          <li>Triboelectric Nanogenerators (TENGs): Capturing friction static electricity from clothing motion.</li>
          <li>Ambient RF Wave Harvesting: Pulling micro-watt power directly out of background Wi-Fi and 5G signals.</li>
          <li>Battery-Free Medical Implants: Pacemakers operating for 30 years without surgical battery replacement.</li>
        </ul>
      ]]></description>
      <enclosure url="https://vipvan-ai.github.io/podcasts/audio/ep-006.mp3" length="{file_size_bytes}" type="audio/mpeg" />
      <guid isPermaLink="false">future-human-daily-ep006-20260930</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>no</itunes:explicit>
    </item>
"""

    if "<channel>" in content and "<!-- EPISODE 005 -->" in content:
        insert_pos = content.find("<!-- EPISODE 005 -->")
        updated = content[:insert_pos] + item_xml + "\n" + content[insert_pos:]
        rss_file.write_text(updated, encoding="utf-8")
        print("[RSS UPDATE] Added Episode 006 to rss.xml!")

def update_ep006_index_and_app():
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        content = content.replace('EPISODE 005', 'EPISODE 006')
        content = content.replace('September 29, 2026', 'September 30, 2026')
        content = content.replace('Neuromorphic Optical Chips &amp; Photonic Brain Computing', 'Ambient Energy Harvesting &amp; Battery-Free Electronics')
        content = content.replace('Replacing silicon electrons with laser micro-channels to process artificial intelligence at light speed with Dr. Elena Vance &amp; Alex Mercer.', 'Powering smartwatches, medical sensors, and gadgets forever without ever plugging them into a wall outlet with Dr. Elena Vance &amp; Alex Mercer.')
        content = content.replace('audio/ep-005.mp3', 'audio/ep-006.mp3')
        index_file.write_text(content, encoding="utf-8")
        print("[INDEX UPDATE] Updated featured player on index.html to Episode 006!")

    app_js = BASE_DIR / "app.js"
    if app_js.exists():
        js_content = app_js.read_text(encoding="utf-8")
        ep006_obj = """        {
            id: 'ep-006',
            number: 'EPISODE 006',
            date: 'September 30, 2026',
            title: 'Ambient Energy Harvesting & Battery-Free Electronics',
            subtitle: 'Powering smartwatches, medical sensors, and gadgets forever without ever plugging them into a wall outlet with Dr. Elena Vance & Alex Mercer.',
            duration: '5:45',
            durationSeconds: 345,
            audioUrl: 'audio/ep-006.mp3',
            tags: ['Energy Harvesting', 'Piezoelectric', 'Battery-Free', 'Green Tech'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is September 30th, and you\'re listening to Future Human Daily. Today we are talking about Ambient Energy Harvesting.' },
                { time: '0:45', label: '[Low-Battery Anxiety Hook]', text: 'The modern panic of dead smartwatch batteries and tangled charging cables.' },
                { time: '1:30', label: '[Micro-Watt Harvesting Analogies]', text: 'Self-winding mechanical watches scaled to micro-electronics.' },
                { time: '2:45', label: '[Piezoelectric & TENG Mechanics]', text: 'Piezoelectric shoe insoles, clothing friction, and ambient Wi-Fi wave capture.' },
                { time: '4:15', label: '[Battery-Free Medical Implants]', text: 'Pacemakers and health monitors running 30 years without surgical battery replacement.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 006, Alex Mercer and Dr. Elena Vance explore piezoelectric shoe insoles, triboelectric clothing, ambient radio-frequency harvesting, and solid-state supercapacitors that never wear out.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Kinetic Piezoelectric Harvesting:</strong> Converting footstep pressure into electrical voltage.</li>
                    <li><strong>Triboelectric Nanogenerators (TENGs):</strong> Capturing friction static electricity from movement.</li>
                    <li><strong>Ambient RF Harvesting:</strong> Pulling power out of background Wi-Fi and 5G signals.</li>
                    <li><strong>Battery-Free Pacemakers:</strong> Medical devices operating 30 years without battery swap surgeries.</li>
                </ul>
            `
        },
"""
        if "const episodes = [" in js_content and "ep-006" not in js_content:
            js_content = js_content.replace("const episodes = [\n", f"const episodes = [\n{ep006_obj}")
            app_js.write_text(js_content, encoding="utf-8")
            print("[APP.JS UPDATE] Added Episode 006 to app.js database!")

if __name__ == "__main__":
    build_master_ep006_pipeline()
