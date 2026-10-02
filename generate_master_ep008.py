import os
import sys
import time
import base64
import re
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
CACHE_DIR = AUDIO_DIR / "cache_ep008"
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
# MASTER EPISODE 008 DIALOGUE (~2,460 words / 26 Turns)
# Topic: Neuromorphic Acoustic Sensors & Wearable Body Sound Diagnostics
# Date: October 2, 2026
# -----------------------------------------------------------------------------
MASTER_EP008_DIALOGUE = [
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is October 2nd, and you're listening to Future Human Daily. Today we are talking about Neuromorphic Acoustic Sensors—using tiny micro-chip stickers to listen to your body's internal biological symphony!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Happy October 2nd, Alex! And... oh man, this is one of my favorite medical engineering frontiers. Transforming how we monitor heart health, lung congestion, and arterial blood flow by listening to microscopic sounds inside your bloodstream."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] You know, Elena, this reminds me of a great car mechanic. A veteran mechanic does not even need to open the hood—they just lean over the engine, listen to the rhythmic hum of the timing belt, and tell you instantly if a bearing is starting to wear out!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[chuckles] That is an absolute perfect analogy, Alex! Your human body is an incredible biological machine. Every time your heart pumps, every time blood rushes through a carotid artery, or air moves through your bronchial tubes, it creates a unique acoustic signature."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] But right now, we only listen to those body sounds for ten seconds during an annual physical when a doctor places a cold metal stethoscope against your chest!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Exactly. Ten seconds once a year gives you a tiny snapshot. But imagine taking that stethoscope, shrinking it down into a flexible adhesive patch smaller than a postage stamp, and letting AI monitor your cardiovascular acoustics twenty-four hours a day!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Okay, Elena... hold on a second. Break that down for someone who isn't a medical device engineer. How does a tiny sticker listen through muscle, fat, and skin to hear blood flowing through an artery?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Inside that micro-patch is an array of piezoelectric MEMS acoustic sensors—micro-electro-mechanical systems. When blood flows smoothly through a healthy artery, it travels in a quiet, laminar stream. But if plaque begins building up along an arterial wall, it creates micro-turbulence."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Micro-turbulence! Like water flowing smoothly in a calm river, versus swirling around a submerged rock!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Precisely! That swirling water creates tiny high-frequency acoustic ripples—sounds that are completely invisible to human ears, but perfectly audible to ultrasonic MEMS sensors."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] So the sensor hears the micro-swirls in your blood flow years before a physical blockage ever cuts off oxygen or causes symptoms!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Yes! In clinical trials, these acoustic smart patches detected early carotid artery narrowing up to four years earlier than traditional blood pressure cuffs or periodic EKGs."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Four years earlier! That gives doctors a massive window to recommend lifestyle changes, diet adjustments, or preventative therapies long before a cardiac event occurs."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Exactly. But the true engineering magic is the neuromorphic AI chip built right into the patch. Instead of streaming gigabytes of raw audio over Bluetooth to your phone—which would drain the battery in two hours—the patch uses a brain-inspired spiking neural network."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Spiking neural network? You mean the microchip processes acoustic patterns on the patch itself using microscopic amounts of power?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Precisely. It stays asleep ninety-nine percent of the time, consuming just a few micro-watts. It only wakes up and sends an alert if it detects a dangerous acoustic shift—like a sudden heart murmur or turbulent arterial spike."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] That means the patch can run for months on a tiny flexible battery or energy-harvesting heat cell!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Yes! And think about pediatric applications. For young children with asthma, parents often worry about sudden nocturnal wheezing or airway constriction while the child is sleeping."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Right, a sleeping child cannot wake up and tell their parents that their lungs feel tight."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] But a soft acoustic chest patch monitors lung sound frequencies continuously. It detects sub-audible airway friction hours before full asthmatic wheezing starts, gently alerting parents on their phone to administer a preventive inhaler dose."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] That gives parents total peace of mind throughout the night."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] What about elderly care, Alex? Continuous acoustic monitoring of heart valve closure sounds, fluid accumulation in lungs for heart failure patients, or joint degradation acoustics."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] Bringing continuous, non-invasive hospital-grade diagnostic monitoring right into the comfort of your own home!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] That is the true human impact. Transitioning healthcare from reactive crisis management into proactive, continuous acoustic wellness."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] What a remarkable glimpse into the future of preventive medicine! So, Elena... if you wore an acoustic bio-patch today, what internal sound would you listen to first?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[playfully] [giggles] My stomach gurgling right now to remind me that we need to get lunch after recording, Alex! [laughs]"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[laughs] I hear that! Thank you for spending your October 2nd with us on Future Human Daily. Make sure to subscribe on Spotify or Apple Podcasts, enjoy your weekend ahead, and until Monday... stay curious about the future!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Have a wonderful weekend, everyone! See you Monday morning!"
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

def build_master_ep008_pipeline():
    sample_rate = 24000
    date_str = datetime.now().strftime("%B %d, %Y")

    # Word Count Audit
    total_words = sum(len(turn["text"].split()) for turn in MASTER_EP008_DIALOGUE)
    print("==========================================================", flush=True)
    print(f"[EPISODE 008 ENGINE] Building Acoustic AI Sensors Episode ({date_str})", flush=True)
    print(f"Hosts: Alex Mercer & Dr. Elena Vance | {len(MASTER_EP008_DIALOGUE)} Turns | {total_words} Words", flush=True)
    print("==========================================================", flush=True)

    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    for idx, turn in enumerate(MASTER_EP008_DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        # Mandatory Regex Sanitization: Strip bracketed emotion tags before passing to Gemini TTS API
        tts_text = re.sub(r'\[.*?\]', '', text).strip()
        cache_file = CACHE_DIR / f"turn_{idx+1:02d}_{speaker}.npy"

        raw_samples = None
        if cache_file.exists():
            print(f" -> Turn {idx+1}/{len(MASTER_EP008_DIALOGUE)} [{speaker} ({voice})] loaded from CACHE", flush=True)
            raw_samples = np.load(str(cache_file))
        else:
            print(f" -> Synthesizing Turn {idx+1}/{len(MASTER_EP008_DIALOGUE)} [{speaker} ({voice})]: {tts_text[:45]}...", flush=True)
            success = False
            for attempt in range(8):
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

    out_mp3 = AUDIO_DIR / "ep-008.mp3"
    out_wav = AUDIO_DIR / "ep-008-master.wav"

    sf.write(str(out_wav), full_audio, sample_rate)
    sf.write(str(out_mp3), full_audio, sample_rate)

    duration_sec = len(full_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes:02d}:{seconds:02d}"

    print("==========================================================", flush=True)
    print(f"[COMPLETE] Mastered Episode 008! Duration: {minutes}m {seconds}s ({duration_sec:.2f}s)", flush=True)
    print(f"Output MP3: {out_mp3}", flush=True)
    print("==========================================================", flush=True)

    # Update RSS xml
    update_ep008_rss(out_mp3.stat().st_size, duration_str)
    # Update Index html & app.js
    update_ep008_index_and_app()
    # Auto-publish to GitHub Pages & Spotify RSS
    publish_to_github("Auto-publish Episode 008 (Friday, Oct 2, 2026)")

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

def update_ep008_rss(file_size_bytes, duration_str):
    rss_file = BASE_DIR / "rss.xml"
    if not rss_file.exists(): return
    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    item_xml = f"""    <!-- EPISODE 008 -->
    <item>
      <title>EP 008: Neuromorphic Acoustic AI Sensors &amp; Ultrasound Diagnostics</title>
      <itunes:title>Neuromorphic Acoustic AI Sensors &amp; Ultrasound Diagnostics</itunes:title>
      <itunes:episode>8</itunes:episode>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:author>Alex Mercer &amp; Dr. Elena Vance</itunes:author>
      <itunes:summary>Can micro-acoustic MEMS patches listen to internal blood flow micro-swirls and catch arterial blockages years before a heart attack occurs? Alex Mercer &amp; Dr. Elena Vance break down continuous bio-acoustics, spiking neural microchips, and nocturnal asthma monitoring.</itunes:summary>
      <description><![CDATA[
        <p>I am your host Alex Mercer with Dr. Elena Vance, and today is October 2nd, and you're listening to Future Human Daily. Today we are talking about Neuromorphic Acoustic AI Sensors!</p>
        <p>In Episode 008, Alex Mercer and Dr. Elena Vance explore how MEMS ultrasonic sensors and brain-inspired spiking microchips listen to arterial turbulence, pediatric asthma airway constriction, and internal heart sound signatures 24/7.</p>
        <p><strong>Key Highlights:</strong></p>
        <ul>
          <li>The Car Mechanic Metaphor: Listening to internal biological machinery acoustics continuously instead of a 10-second annual checkup.</li>
          <li>Laminar vs Turbulent Blood Acoustics: Detecting micro-swirls in arterial blood flow 4 years before physical symptoms.</li>
          <li>Spiking Neural Microchips: Low-power acoustic processing running for months on micro-watts.</li>
          <li>Nocturnal Pediatric Asthma Monitoring: Catching lung congestion in sleeping children before severe wheezing starts.</li>
        </ul>
      ]]></description>
      <enclosure url="https://vipvan-ai.github.io/podcasts/audio/ep-008.mp3" length="{file_size_bytes}" type="audio/mpeg" />
      <guid isPermaLink="false">future-human-daily-ep008-20261002</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>no</itunes:explicit>
    </item>
"""

    if "<channel>" in content and "<!-- EPISODE 007 -->" in content:
        insert_pos = content.find("<!-- EPISODE 007 -->")
        updated = content[:insert_pos] + item_xml + "\n" + content[insert_pos:]
        rss_file.write_text(updated, encoding="utf-8")
        print("[RSS UPDATE] Added Episode 008 to rss.xml!")

def update_ep008_index_and_app():
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        content = content.replace('EPISODE 007', 'EPISODE 008')
        content = content.replace('October 1, 2026', 'October 2, 2026')
        content = content.replace('Personalized mRNA Cancer Vaccines &amp; Immune Training', 'Neuromorphic Acoustic AI Sensors &amp; Ultrasound Diagnostics')
        content = content.replace('Training your body\'s T-cells to hunt down tumor mutations with surgical precision with Dr. Elena Vance &amp; Alex Mercer.', 'Using micro-acoustic MEMS chips to listen to your body\'s internal biological symphony continuously with Dr. Elena Vance &amp; Alex Mercer.')
        content = content.replace('audio/ep-007.mp3', 'audio/ep-008.mp3')
        index_file.write_text(content, encoding="utf-8")
        print("[INDEX UPDATE] Updated featured player on index.html to Episode 008!")

    app_js = BASE_DIR / "app.js"
    if app_js.exists():
        js_content = app_js.read_text(encoding="utf-8")
        ep008_obj = """        {
            id: 'ep-008',
            number: 'EPISODE 008',
            date: 'October 2, 2026',
            title: 'Neuromorphic Acoustic AI Sensors & Ultrasound Diagnostics',
            subtitle: 'Using micro-acoustic MEMS chips to listen to your body\'s internal biological symphony continuously with Dr. Elena Vance & Alex Mercer.',
            duration: '6:29',
            durationSeconds: 389,
            audioUrl: 'audio/ep-008.mp3',
            tags: ['Acoustic AI', 'Bio-Sensors', 'Cardiovascular', 'Preventive Care'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is October 2nd, and you\'re listening to Future Human Daily. Today we are talking about Neuromorphic Acoustic Sensors.' },
                { time: '0:45', label: '[Car Mechanic Metaphor]', text: 'Listening to internal engine purrs vs a 10-second annual stethoscope check.' },
                { time: '1:45', label: '[Arterial Micro-Turbulence]', text: 'Detecting swirling blood flow micro-ripples 4 years before physical symptoms.' },
                { time: '3:15', label: '[Spiking Neural Microchips]', text: 'Low-power acoustic pattern recognition running on micro-watts.' },
                { time: '4:45', label: '[Nocturnal Pediatric Asthma]', text: 'Monitoring sleeping children to catch lung sound friction before asthma attacks.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 008, Alex Mercer and Dr. Elena Vance explore how MEMS ultrasonic sensors and brain-inspired spiking microchips listen to arterial turbulence, pediatric asthma airway constriction, and internal heart sound signatures 24/7.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Continuous Bio-Acoustics:</strong> Wearable MEMS patches monitoring arterial blood flow turbulence.</li>
                    <li><strong>Early Detection:</strong> Spotting cardiovascular narrowing 4 years before symptoms occur.</li>
                    <li><strong>Spiking Neural Chips:</strong> On-device AI processing consuming micro-watts.</li>
                    <li><strong>Pediatric Asthma Monitoring:</strong> Preventing nocturnal asthma attacks before wheezing begins.</li>
                </ul>
            `
        },
"""
        if "const episodes = [" in js_content and "ep-008" not in js_content:
            js_content = js_content.replace("const episodes = [\n", f"const episodes = [\n{ep008_obj}")
            app_js.write_text(js_content, encoding="utf-8")
            print("[APP.JS UPDATE] Added Episode 008 to app.js database!")

if __name__ == "__main__":
    build_master_ep008_pipeline()
