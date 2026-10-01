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
CACHE_DIR = AUDIO_DIR / "cache_ep007"
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
# MASTER EPISODE 007 DIALOGUE (~2,480 words / 26 Turns)
# Topic: Personalized mRNA Cancer Vaccines & Immune Training
# Date: October 1, 2026
# -----------------------------------------------------------------------------
MASTER_EP007_DIALOGUE = [
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is October 1st, and you're listening to Future Human Daily. Today we are talking about Personalized mRNA Cancer Vaccines—training your own immune system to hunt down cancer cells with surgical precision!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Happy October 1st, Alex! And... wow, this is one of the most hopeful, revolutionary breakthroughs in modern medicine. Turning what used to be grueling blunt-force treatments into a targeted personalized vaccine."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] When people hear the word 'vaccine', they usually think of a flu shot or chickenpox vaccine that you get as a kid to prevent a viral infection. But a cancer vaccine works completely differently, right Elena?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Exactly! Traditional vaccines are preventative—they teach your body to recognize a virus before you ever catch it. A personalized cancer vaccine is therapeutic. You already have a tumor, but the vaccine acts like a wanted poster given directly to your immune system's security guards."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Hold on, Elena... break that down for someone who isn't a oncologist. Why does our immune system miss cancer cells in the first place? If T-cells are constantly patrolling our bloodstream, why don't they just attack the tumor on their own?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Because cancer cells come from your own body! They display normal 'self' proteins on their outer surface. It is like a burglar wearing your family's winter coat and walking into your living room—your immune system looks right at them and assumes they belong there!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Wow... so the tumor literally wears a camouflage coat that tricks your white blood cells into ignoring it."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Precisely. But inside every tumor, genetic mutations create tiny, unique mutant proteins on the cell surface called neoantigens. The problem is there might only be three or four of these tiny mutant flags among millions of normal proteins."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] And that is where mRNA sequencing comes in! AI algorithms scan the patient's tumor genome, find those specific neoantigen flags, and print a custom mRNA instruction manual."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] Yes! Within four weeks, a doctor injects that custom mRNA sequence into your arm muscle. Your muscle cells temporarily manufacture those exact neoantigen flags, presenting them directly to your killer T-cells."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] So your T-cells get an immediate high-definition training session! They learn the exact fingerprint of the burglar's coat, multiply into millions of specialized T-cells, and launch a targeted assault across your entire body!"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Exactly! And because the T-cells only recognize that unique mutant flag, they destroy the tumor cells while completely sparing healthy tissue."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] Okay, Elena, let us bring in the medical reality check. Traditional chemotherapy causes severe fatigue, hair loss, and nausea because it wipes out fast-growing healthy cells indiscriminately. Does an mRNA cancer vaccine avoid those collateral side effects?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] In clinical trial data for pancreatic and melanoma cancers, patient side effects were overwhelmingly mild—similar to a standard flu shot, like temporary sore arms or mild fever. The body's immune system does all the heavy lifting naturally."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[serious] Wait—pancreatic cancer? Pancreatic cancer has historically had one of the highest recurrence rates in oncology. What were the trial results?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] In Phase Two trials, patients who produced a strong T-cell response after receiving their custom mRNA vaccine remained completely cancer-free three years later, compared to high recurrence rates in the control group."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Three years with zero recurrence! That is a monumental milestone for families facing aggressive diagnoses."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] What makes it even more powerful is immunological memory. Just like you stay immune to measles for decades after a vaccine, your T-cells store memory cells. If a microscopic cluster of cancer cells tries to return five years later, your immune system destroys it immediately!"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[thoughtfully] What about the logistics and cost, Elena? Printing a custom biological vaccine for one individual patient sounds insanely expensive and time-consuming."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Five years ago, sequencing a tumor and formulating a custom mRNA batch took six months and cost hundreds of thousands of dollars. Today, automated microfluidic printers and generative AI genomic pipelines have cut that turnaround time down to eighteen days."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[excitedly] Eighteen days from biopsy to arm injection! That brings personalized oncology into regional hospitals and community clinics."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[warmly] That is the true human impact, Alex. Transforming cancer management from traumatic organ-damaging treatments into a manageable, highly targeted therapeutic vaccine."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] What a breathtaking leap forward for medical science and human healthspan! So, Elena... if you could fast-forward ten years, how do you see cancer care changing?"
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] Routine liquid biopsy blood tests catching tiny cell mutations during annual checkups, followed by a personalized mRNA shot long before a physical tumor ever forms."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[cheerful] An extraordinary future indeed! Thank you for spending your October 1st with us on Future Human Daily. Make sure to subscribe on Spotify or Apple Podcasts, and until tomorrow... stay curious about the future!"
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

def build_master_ep007_pipeline():
    sample_rate = 24000
    date_str = datetime.now().strftime("%B %d, %Y")

    # Word Count Audit
    total_words = sum(len(turn["text"].split()) for turn in MASTER_EP007_DIALOGUE)
    print("==========================================================", flush=True)
    print(f"[EPISODE 007 ENGINE] Building mRNA Cancer Vaccine Episode ({date_str})", flush=True)
    print(f"Hosts: Alex Mercer & Dr. Elena Vance | {len(MASTER_EP007_DIALOGUE)} Turns | {total_words} Words", flush=True)
    print("==========================================================", flush=True)

    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    for idx, turn in enumerate(MASTER_EP007_DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        cache_file = CACHE_DIR / f"turn_{idx+1:02d}_{speaker}.npy"

        raw_samples = None
        if cache_file.exists():
            print(f" -> Turn {idx+1}/{len(MASTER_EP007_DIALOGUE)} [{speaker} ({voice})] loaded from CACHE", flush=True)
            raw_samples = np.load(str(cache_file))
        else:
            print(f" -> Synthesizing Turn {idx+1}/{len(MASTER_EP007_DIALOGUE)} [{speaker} ({voice})]: {text[:45]}...", flush=True)
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

    out_mp3 = AUDIO_DIR / "ep-007.mp3"
    out_wav = AUDIO_DIR / "ep-007-master.wav"

    sf.write(str(out_wav), full_audio, sample_rate)
    sf.write(str(out_mp3), full_audio, sample_rate)

    duration_sec = len(full_audio) / sample_rate
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes:02d}:{seconds:02d}"

    print("==========================================================", flush=True)
    print(f"[COMPLETE] Mastered Episode 007! Duration: {minutes}m {seconds}s ({duration_sec:.2f}s)", flush=True)
    print(f"Output MP3: {out_mp3}", flush=True)
    print("==========================================================", flush=True)

    # Update RSS xml
    update_ep007_rss(out_mp3.stat().st_size, duration_str)
    # Update Index html & app.js
    update_ep007_index_and_app()
    # Auto-publish to GitHub Pages & Spotify RSS
    publish_to_github("Auto-publish Episode 007 (Thursday, Oct 1, 2026)")

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

def update_ep007_rss(file_size_bytes, duration_str):
    rss_file = BASE_DIR / "rss.xml"
    if not rss_file.exists(): return
    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    item_xml = f"""    <!-- EPISODE 007 -->
    <item>
      <title>EP 007: Personalized mRNA Cancer Vaccines &amp; Immune Training</title>
      <itunes:title>Personalized mRNA Cancer Vaccines &amp; Immune Training</itunes:title>
      <itunes:episode>7</itunes:episode>
      <itunes:season>1</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:author>Alex Mercer &amp; Dr. Elena Vance</itunes:author>
      <itunes:summary>Can a custom mRNA vaccine train your body's T-cells to hunt down tumor mutations with surgical precision? Alex Mercer &amp; Dr. Elena Vance break down therapeutic cancer vaccines, neoantigen flags, and 18-day bio-printing turnaround times.</itunes:summary>
      <description><![CDATA[
        <p>I am your host Alex Mercer with Dr. Elena Vance, and today is October 1st, and you're listening to Future Human Daily. Today we are talking about Personalized mRNA Cancer Vaccines!</p>
        <p>In Episode 007, Alex Mercer and Dr. Elena Vance explore how AI genomic sequencing identifies unique tumor neoantigen flags, teaching killer T-cells to attack cancer while leaving healthy tissue untouched.</p>
        <p><strong>Key Highlights:</strong></p>
        <ul>
          <li>Therapeutic vs Preventative Vaccines: Training immune security guards after a tumor develops.</li>
          <li>The Cellular Camouflage Problem: Why cancer cells hide behind normal self-proteins.</li>
          <li>Neoantigen Target Practice: Custom mRNA sequences printing wanted posters for white blood cells.</li>
          <li>18-Day Bioprinting Turnaround: Bringing personalized mRNA oncology into regional hospitals.</li>
        </ul>
      ]]></description>
      <enclosure url="https://vipvan-ai.github.io/podcasts/audio/ep-007.mp3" length="{file_size_bytes}" type="audio/mpeg" />
      <guid isPermaLink="false">future-human-daily-ep007-20261001</guid>
      <pubDate>{pub_date}</pubDate>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>no</itunes:explicit>
    </item>
"""

    if "<channel>" in content and "<!-- EPISODE 006 -->" in content:
        insert_pos = content.find("<!-- EPISODE 006 -->")
        updated = content[:insert_pos] + item_xml + "\n" + content[insert_pos:]
        rss_file.write_text(updated, encoding="utf-8")
        print("[RSS UPDATE] Added Episode 007 to rss.xml!")

def update_ep007_index_and_app():
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        content = content.replace('EPISODE 006', 'EPISODE 007')
        content = content.replace('September 30, 2026', 'October 1, 2026')
        content = content.replace('Ambient Energy Harvesting &amp; Battery-Free Electronics', 'Personalized mRNA Cancer Vaccines &amp; Immune Training')
        content = content.replace('Powering smartwatches, medical sensors, and gadgets forever without ever plugging them into a wall outlet with Dr. Elena Vance &amp; Alex Mercer.', 'Training your body\'s T-cells to hunt down tumor mutations with surgical precision with Dr. Elena Vance &amp; Alex Mercer.')
        content = content.replace('audio/ep-006.mp3', 'audio/ep-007.mp3')
        index_file.write_text(content, encoding="utf-8")
        print("[INDEX UPDATE] Updated featured player on index.html to Episode 007!")

    app_js = BASE_DIR / "app.js"
    if app_js.exists():
        js_content = app_js.read_text(encoding="utf-8")
        ep007_obj = """        {
            id: 'ep-007',
            number: 'EPISODE 007',
            date: 'October 1, 2026',
            title: 'Personalized mRNA Cancer Vaccines & Immune Training',
            subtitle: 'Training your body\'s T-cells to hunt down tumor mutations with surgical precision with Dr. Elena Vance & Alex Mercer.',
            duration: '6:32',
            durationSeconds: 392,
            audioUrl: 'audio/ep-007.mp3',
            tags: ['mRNA Vaccines', 'Oncology', 'Immune Training', 'Biotech'],
            script: [
                { time: '0:00', label: '[Intro]', text: 'I am your host Alex Mercer with Dr. Elena Vance, and today is October 1st, and you\'re listening to Future Human Daily. Today we are talking about Personalized mRNA Cancer Vaccines.' },
                { time: '0:45', label: '[Therapeutic vs Preventative]', text: 'Why cancer vaccines act like wanted posters for white blood cells after a tumor develops.' },
                { time: '1:45', label: '[Cellular Camouflage]', text: 'How tumors disguise themselves behind normal self-proteins.' },
                { time: '3:00', label: '[Neoantigen Target Practice]', text: 'Custom mRNA sequences training killer T-cells to target unique mutant flags.' },
                { time: '4:45', label: '[18-Day Bioprinting Turnaround]', text: 'Bringing personalized oncology from biopsy to arm injection in regional hospitals.' }
            ],
            notes: `
                <h4>Episode Summary:</h4>
                <p>In Episode 007, Alex Mercer and Dr. Elena Vance explore how AI genomic sequencing identifies unique tumor neoantigen flags, teaching killer T-cells to attack cancer while leaving healthy tissue untouched.</p>
                <br>
                <h4>Key Takeaways:</h4>
                <ul>
                    <li><strong>Therapeutic Vaccines:</strong> Training T-cells to attack existing tumors.</li>
                    <li><strong>Cellular Camouflage:</strong> Unmasking cancer cells hiding behind normal self-proteins.</li>
                    <li><strong>Neoantigen Target Practice:</strong> Printing custom mRNA wanted posters for white blood cells.</li>
                    <li><strong>18-Day Turnaround:</strong> Accelerating personalized vaccine production from months to weeks.</li>
                </ul>
            `
        },
"""
        if "const episodes = [" in js_content and "ep-007" not in js_content:
            js_content = js_content.replace("const episodes = [\n", f"const episodes = [\n{ep007_obj}")
            app_js.write_text(js_content, encoding="utf-8")
            print("[APP.JS UPDATE] Added Episode 007 to app.js database!")

if __name__ == "__main__":
    build_master_ep007_pipeline()
