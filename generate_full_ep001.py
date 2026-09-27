import subprocess
import os
from pathlib import Path

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

script_text = """Imagine sitting across from someone you love. No words are spoken. No fingers tap on a screen. Yet in a fraction of a second, an entire concept, a vivid memory, a precise emotional state, or a complex technical blueprint is transmitted directly from your mind into theirs.

This isn't science fiction. It is the emerging science of Synthetic Telepathy, enabled by high-bandwidth Brain-Computer Interfaces.

Welcome to Future Human Daily. I'm your host, and today, we're exploring what happens when human thought escapes the boundaries of language.

For all of human history, communication has suffered from a fundamental bottleneck: bandwidth. Your brain processes thoughts at lightning speed, with millions of neurons firing in high-dimensional complexity. But to share a thought, you must squeeze it down through vocal cords or your fingertips at a painfully slow rate of roughly 40 to 60 words per minute.

Enter modern BCIs. Companies like Neuralink, Synchron, and Paradromics are developing ultra-thin neural threads capable of reading thousands of individual action potentials directly from the motor and language cortex.

When neural implants can both read and write signals to the cortex with sub-millisecond precision, we unlock direct brain-to-brain synthesis. Imagine empathy without translation: sharing the exact feeling of an emotion rather than trying to describe it in words. Or collaborative genius: where engineers, surgeons, and artists merge mental workspaces in real time.

Language was just our first operating system. The next OS will be direct neural resonance.

Thank you for joining today's journey into tomorrow on Future Human Daily. What thought would you share if words didn't exist? Subscribe on Spotify or Apple Podcasts, and until tomorrow, stay curious about the future."""

txt_file = AUDIO_DIR / "ep-001-text.txt"
mp3_file = AUDIO_DIR / "ep-001.mp3"

with open(txt_file, "w", encoding="utf-8") as f:
    f.write(script_text)

print("[Audio Engine] Generating full Episode 001 audio via Microsoft Edge Neural TTS (en-US-AndrewNeural)...")
cmd = [
    "edge-tts",
    "--file", str(txt_file),
    "--voice", "en-US-AndrewNeural",
    "--rate", "+4%",
    "--pitch", "+2Hz",
    "--write-media", str(mp3_file)
]

result = subprocess.run(cmd, capture_output=True, text=True)
if mp3_file.exists() and mp3_file.stat().st_size > 1000:
    print(f"[Success] Generated ep-001.mp3 successfully ({mp3_file.stat().st_size / 1024:.1f} KB)")
else:
    print(f"[Error] Failed: {result.stderr}")
