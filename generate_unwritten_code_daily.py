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
    return None

def update_unwritten_code_rss(ep_number, ep_title, ep_summary, mp3_filename, duration_str, file_size_bytes):
    rss_file = BASE_DIR / "unwritten_code_rss.xml"
    if not rss_file.exists():
        print("[RSS ERROR] unwritten_code_rss.xml not found!", flush=True)
        return False

    content = rss_file.read_text(encoding="utf-8")
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    guid = f"unwritten-code-ep-{ep_number:03d}-{datetime.now().strftime('%Y%m%d')}"

    clean_title = ep_title.replace('&', '&amp;') if '&amp;' not in ep_title else ep_title
    clean_summary = ep_summary.replace('&', '&amp;') if '&amp;' not in ep_summary else ep_summary

    new_item = f"""    <!-- EPISODE {ep_number:03d} -->
    <item>
      <title>{clean_title}</title>
      <itunes:title>{clean_title}</itunes:title>
      <itunes:episode>{ep_number}</itunes:episode>
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

    marker = "<!-- OFFICIAL TRAILER"
    if marker in content:
        insert_idx = content.find(marker)
        updated_content = content[:insert_idx] + new_item + "\n    " + content[insert_idx:]
    else:
        insert_idx = content.find("</channel>")
        updated_content = content[:insert_idx] + new_item + content[insert_idx:]

    rss_file.write_text(updated_content, encoding="utf-8")
    print(f"[RSS SUCCESS] Added Episode {ep_number} to unwritten_code_rss.xml!", flush=True)
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
# EPISODE SCRIPTS DATABASE BY DAY OF WEEK
# =============================================================================
def get_script_for_day(day_idx):
    """Returns (episode_number, title, summary, script_turns) based on weekday."""
    # Monday = 0: Workplace & Slack Etiquette
    if day_idx == 0:
        ep_num = 1
        title = "EP 001: The Slack Thumbs-Up vs. The Reply-All Disaster"
        summary = "Maya & Julian launch The Unwritten Code by unpacking modern workplace messaging anxiety: why does a thumbs-up emoji on Slack feel passive-aggressive, the agony of the 'No-Hello' typing bubble, and who is still hitting reply-all to company emails?"
        turns = [
            {"speaker": "Maya", "voice": "Kore", "text": "[cheerful] Happy Monday, everyone! Welcome to the official premiere of The Unwritten Code! I am Maya Lin, and if you are listening to this on your morning commute, sitting at your desk with your second cup of coffee, or hiding in the office kitchen avoiding your inbox, you are in the exact right place. Today is Monday, October fifth, which means we are inaugurating this show by diving headfirst into the chaotic, passive-aggressive jungle known as modern workplace communication."},
            {"speaker": "Julian", "voice": "Puck", "text": "[warmly] And I am Julian Cross. Maya, I have to say, there is no better way to kick off Episode One than with the corporate danger zone. Every single one of us spends forty to fifty hours a week staring at glowing screens, deciphering micro-messages, decoding emoji nuances, and pretending we understand what our coworkers actually mean when they type three innocent words. Society spent thousands of years developing vocal tone, facial expressions, and body language, and then within ten years, corporate software compressed all human intimacy down into unformatted text bubbles on Slack and Teams."},
            {"speaker": "Maya", "voice": "Kore", "text": "[playfully] It really is an emotional battlefield! And the single biggest flashpoint in the modern office right now is one humble, yellow digital icon: the Slack thumbs-up emoji. Julian, let me set the scene for you. An employee spends three solid hours pouring their heart, soul, and intellect into a comprehensive, beautifully structured project update. They hit send, their pulse is racing, and two minutes later, their manager reacts with a single, naked, yellow thumbs-up emoji. Tell me: what is the psychological fallout of that moment?"},
            {"speaker": "Julian", "voice": "Puck", "text": "[chuckles] Absolute existential terror, Maya! My heart plunges straight through the floorboards. I immediately minimize the window, stare blankly out the window, and spend the next forty-five minutes frantically re-reading every single syllable of my update to figure out if I am about to get fired, demoted, or placed on a secret performance improvement plan! [sighs] The thumbs-up emoji is the most emotionally ambiguous gesture in human history. Does it mean Great job? Does it mean I acknowledge your existence? Or does it mean I am deeply disappointed in you, but I do not have the patience to type real words?"},
            {"speaker": "Maya", "voice": "Kore", "text": "[laughs] That is the genius and the horror of it! What we have here is the great generational divide of the corporate world. If you talk to anyone in senior leadership who grew up with flip phones and fax machines, a thumbs-up emoji is the pinnacle of workplace efficiency. To them, it simply means: Message received, thank you, keep moving. But to anyone under thirty-five, receiving a lone thumbs-up feels like someone looked you directly in the eyes in the hallway, said nothing, and slowly closed the elevator door in your face with a blank expression!"},
            {"speaker": "Julian", "voice": "Puck", "text": "[laughs] [warmly] It has zero emotional warmth, Maya! It is cold, robotic, and transactional. It is the digital equivalent of texting someone the letter K with a period at the end! If you receive a text from a friend that says K with a period, you immediately assume the friendship is over and they are blocking your number. The thumbs-up carries that exact same chilling energy in a direct message. If you want to encourage your team, use the celebration party popper! Use the green checkmark! Use the little dancing penguin! Use literally anything in the emoji library except the cold, unfeeling thumb of doom!"},
            {"speaker": "Maya", "voice": "Kore", "text": "[playfully] I could not agree more, Julian! But wait, because workplace messaging crimes do not stop at emojis. Let us talk about what I call the Hello Hostage Situation. You are sitting at your desk, deep in your zone, making actual progress on a spreadsheet. Suddenly, your notification dings: Dave from Marketing says: Hey Maya. And then... nothing. Silence. Just that little pencil icon bouncing: Dave is typing... Dave stopped typing... Dave is typing again. Julian, why do people do this?!"},
            {"speaker": "Julian", "voice": "Puck", "text": "[chuckles] Oh, it is psychological torture! Why are you holding my attention hostage with a two-word greeting? Tell me what you want in the same breath! When someone sends just Hey Julian, they are demanding that I stop whatever I am doing, reply with Hey Dave, and wait for them to spend three agonizing minutes composing their actual question. There is a whole website dedicated to this called No Hello! Just type: Hey Julian, quick question about the budget numbers, do you have five minutes later today? Boom, done, professional, respectful of my sanity!"},
            {"speaker": "Maya", "voice": "Kore", "text": "[laughs] Exactly! Respect the time and respect the nervous system! But now, Julian, we have to address the undisputed heavyweight champion of workplace felonies. The crime against humanity that unites every corporate department from sales to engineering in collective agony: The Reply-All Disaster."},
            {"speaker": "Julian", "voice": "Puck", "text": "[groans] [chuckles] Oh, heaven help us! Straight to corporate federal prison! Maya, walk us through how this horror show always unfolds."},
            {"speaker": "Maya", "voice": "Kore", "text": "[playfully] It always starts completely innocently. Human Resources or the Facilities team sends an email announcement to two thousand people across four global offices: Reminder: The cafeteria will be serving pumpkin soup this Thursday. Simple, right? But then, within ninety seconds, someone named Kevin in Regional Logistics accidentally clicks Reply-All instead of Reply, and broadcasts to all two thousand people: Sounds delicious, thanks team! And that is when the nuclear chain reaction begins."},
            {"speaker": "Julian", "voice": "Puck", "text": "[laughs] Because thirty seconds later, three different people who think they are the email police hit Reply-All to say: Please stop replying all to this thread! And then five minutes later, eight more people hit Reply-All screaming: Why am I on this list? Please unsubscribe me! And within half an hour, the company exchange server is smoking in the IT closet, forty thousand redundant emails have clogged everyone's inboxes, and productive work has ground to a complete halt across three time zones!"},
            {"speaker": "Maya", "voice": "Kore", "text": "[giggles] It is a self-sustaining cyclone of office madness! I once worked at an agency where a reply-all chain got so completely out of control that someone started replying all with sourdough bread recipes, another person attached photos of their golden retriever, and leadership had to send an emergency IT kill-switch memo shutting down the entire email server for the afternoon!"},
            {"speaker": "Julian", "voice": "Puck", "text": "[chuckles] See, this is why modern society is crumbling at the edges, Maya! We have sophisticated artificial intelligence, quantum computing, and autonomous electric vehicles, but human beings still cannot resist the primal urge to hit Reply-All and inform four thousand strangers that they enjoy pumpkin soup!"},
            {"speaker": "Maya", "voice": "Kore", "text": "[playfully] And speaking of virtual workplace drama, Julian, what about modern meeting culture? Specifically, the awkward Camera-On Standoff. You log into a nine AM video call with your camera politely turned off, wearing a comfy hoodie and holding your tea, and the meeting host chirps: Hey everyone, let us all turn our cameras on so we can see all your lovely smiling faces this morning!"},
            {"speaker": "Julian", "voice": "Puck", "text": "[sighs] [chuckles] The sheer panic! Your fight-or-flight response kicks in immediately! You are frantically scrambling to throw a collared dress shirt over your pajama pants, wiping sleep out of your eyes, kicking laundry baskets out of the webcam frame, and desperately toggling the background blur filter hoping it disguises the fact that you are sitting on your unmade bed!"},
            {"speaker": "Maya", "voice": "Kore", "text": "[laughs] And the funniest secret of all, Julian, is that nobody on a video call is actually looking at the person speaking anyway! Behavioral studies have shown that during an eight-person Zoom meeting, people spend roughly eighty-five percent of the time staring exclusively at their own tiny video preview box in the corner, making sure their hair looks acceptable and adjusting their chin angle!"},
            {"speaker": "Julian", "voice": "Puck", "text": "[laughs] It is pure vanity under the guise of collaboration! And of course, there is always the grand finale of every video meeting: the person who delivers an impassioned, three-minute speech on quarterly revenue while completely muted, gesturing wildly with their hands, until six people simultaneously unmute to scream: Bob, you are on mute! Bob, we cannot hear you!"},
            {"speaker": "Maya", "voice": "Kore", "text": "[cheerful] Every single day, Julian! Which is why we created The Unwritten Code. Because somebody has to bring law, order, and sanity to the modern human experience. So right here on Episode One, let us officially hand down The New Code for surviving modern workplace communication."},
            {"speaker": "Julian", "voice": "Puck", "text": "[warmly] Here is The Code. Rule Number One: The Emoji Upgrade Law. If you manage people, ban the naked thumbs-up emoji on Slack forever. If you want to acknowledge good work, use the green checkmark, the party popper, or pair your thumbs-up with three actual words like: Looks great, thanks! Save a life; upgrade your emoji."},
            {"speaker": "Maya", "voice": "Kore", "text": "[playfully] Rule Number Two: The No-Hello Mandate. Never send a standalone greeting. Always include your actual request or question in the very same message. Your coworkers will respect you, your projects will move faster, and nobody has to stare at the bouncing typing bubble in terror."},
            {"speaker": "Julian", "voice": "Puck", "text": "[chuckles] Rule Number Three: The Reply-All Felony Fine. If you reply-all to a company-wide announcement sent to more than twenty people just to say thanks or ask to be unsubscribed, you are officially obligated to buy gourmet coffee and donuts for your entire department on Friday morning."},
            {"speaker": "Maya", "voice": "Kore", "text": "[warmly] And Rule Number Four: The Three-Sentence Email Boundary. If an email thread requires more than three back-and-forth messages, stop typing paragraphs. Pick up the phone or walk over for a sixty-second conversation. Protect your inbox sanity!"},
            {"speaker": "Julian", "voice": "Puck", "text": "[warmly] That is The Unwritten Code for this Monday morning! What an incredible way to kick off our very first episode. If you resonated with any of these workplace struggles, do not forget to hit the Follow button right now on Spotify and Apple Podcasts so you never miss tomorrow morning's drop!"},
            {"speaker": "Maya", "voice": "Kore", "text": "[cheerful] Tomorrow on Tuesday, we are leaving the office behind and diving straight into modern dating economics: who pays on date three, the awkward wallet reach, and why the slow-fade text is worse than ghosting. Until tomorrow morning, stay sane out there, and remember: do not break the code!"}
        ]
        return ep_num, title, summary, turns

    # Tuesday = 1: Modern Dating & Romance
    elif day_idx == 1:
        ep_num = 2
        title = "EP 002: Who Pays on Date Three? (And The Ghosting Slow-Fade)"
        summary = "Maya & Julian unpack modern dating etiquette: who pays on date three, the awkward wallet reach, and why the slow-fade text is worse than outright ghosting."
        turns = [
            {"speaker": "Maya", "voice": "Kore", "text": "[cheerful] Welcome back to The Unwritten Code! I am Maya Lin with Julian Cross, and today is Tuesday—which means we are diving into the messy, confusing battlefield of modern romance."},
            {"speaker": "Julian", "voice": "Puck", "text": "[chuckles] Oh boy. Today's dilemma comes straight from a listener who asked: on date three, who is responsible for picking up the dinner tab?"},
            {"speaker": "Maya", "voice": "Kore", "text": "[playfully] The classic wallet showdown! Date one, whoever asked usually pays. Date two, the other person offers. But on date three, you hit this weird financial stalemate."},
            {"speaker": "Julian", "voice": "Puck", "text": "[warmly] [chuckles] Exactly. You do the polite fake-reach for your card, but secretly you are praying the other person insists!"},
            {"speaker": "Maya", "voice": "Kore", "text": "[laughs] And let us talk about the slow-fade text! Leaving someone on read for three days instead of just saying: 'Hey, I had fun, but I didn't feel a romantic spark.'"},
            {"speaker": "Julian", "voice": "Puck", "text": "[warmly] That is The Unwritten Code for Tuesday! Be honest, split the third date, and never do the slow-fade. See you tomorrow!"}
        ]
        return ep_num, title, summary, turns

    # Default fallback for other weekdays
    else:
        ep_num = day_idx + 1
        title = f"EP 00{ep_num}: Modern Social Dynamics & Everyday Rules"
        summary = "Maya & Julian unpack life's unwritten rules and modern etiquette."
        turns = [
            {"speaker": "Maya", "voice": "Kore", "text": "[cheerful] Welcome back to The Unwritten Code with Maya Lin and Julian Cross!"},
            {"speaker": "Julian", "voice": "Puck", "text": "[warmly] Today we are breaking down life's unspoken social contracts. Let's get into it!"},
            {"speaker": "Maya", "voice": "Kore", "text": "[playfully] Have you ever wondered why people behave the way they do in public?"},
            {"speaker": "Julian", "voice": "Puck", "text": "[chuckles] That is why we are here. Don't break the code!"}
        ]
        return ep_num, title, summary, turns

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
    out_mp3_name = f"unwritten_code_ep{ep_num:03d}_{date_tag}.mp3"
    out_wav_name = f"unwritten_code_ep{ep_num:03d}_{date_tag}.wav"
    out_mp3 = AUDIO_DIR / out_mp3_name
    out_wav = AUDIO_DIR / out_wav_name

    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.32), dtype=np.float32)

    for idx, turn in enumerate(script_turns):
        cache_key = f"ep{ep_num:03d}_{date_tag}_turn_{idx+1}_{turn['speaker']}"
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
    update_unwritten_code_rss(ep_num, ep_title, ep_summary, out_mp3_name, duration_str, file_size)

    # 2. Push to GitHub Pages & Spotify RSS
    auto_publish_to_github(f"Auto-publish {ep_title} ({date_str})")

    print("\n==========================================================", flush=True)
    print(f"[COMPLETE] Episode {ep_num} published successfully!", flush=True)
    print("==========================================================", flush=True)
    return True

if __name__ == "__main__":
    run_daily_pipeline()
