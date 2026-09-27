import subprocess
import os
from pathlib import Path

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Rich SSML XML with vocal style, emphasis, natural breathing breaks, and rate/pitch dynamics
ssml_content = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
  <voice name="en-US-AndrewNeural">
    <mstts:express-as style="cheerful" styledegree="1.2">
      Imagine sitting across from someone you love. <break time="400ms"/> No words are spoken. <break time="350ms"/> No fingers tap on a screen. 
    </mstts:express-as>
    <break time="450ms"/>
    <mstts:express-as style="excited" styledegree="1.3">
      <prosody rate="+3%" pitch="+2Hz">
        Yet in a fraction of a second, an entire concept—a vivid memory, a precise emotional state, or a complex technical blueprint—is transmitted directly from your mind into theirs!
      </prosody>
    </mstts:express-as>
    <break time="600ms"/>

    <mstts:express-as style="serious" styledegree="1.1">
      This isn't science fiction. <break time="300ms"/> It is the emerging science of <prosody pitch="+3Hz">Synthetic Telepathy</prosody>, enabled by high-bandwidth Brain-Computer Interfaces.
    </mstts:express-as>
    <break time="700ms"/>

    <mstts:express-as style="newscast" styledegree="1.2">
      Welcome to <prosody pitch="+2Hz" rate="+2%">Future Human Daily</prosody>. I'm your host, and today, we're exploring what happens when human thought escapes the boundaries of language.
    </mstts:express-as>
    <break time="750ms"/>

    <mstts:express-as style="serious" styledegree="1.2">
      For all of human history, communication has suffered from a fundamental bottleneck: <prosody pitch="-2Hz">bandwidth</prosody>. <break time="400ms"/>
      Your brain processes thoughts at lightning speed—millions of neurons firing in high-dimensional complexity. But to share a thought, you must squeeze it down through vocal cords or fingertips at a painfully slow rate of roughly 40 to 60 words per minute.
    </mstts:express-as>
    <break time="650ms"/>

    <mstts:express-as style="excited" styledegree="1.2">
      Enter modern BCIs! <break time="300ms"/> Companies like Neuralink, Synchron, and Paradromics are developing ultra-thin neural threads capable of reading thousands of individual action potentials directly from the language cortex.
    </mstts:express-as>
    <break time="600ms"/>

    <mstts:express-as style="empathetic" styledegree="1.3">
      When neural implants can both read and write signals to the cortex with sub-millisecond precision, we unlock direct brain-to-brain synthesis. <break time="400ms"/>
      Imagine <prosody pitch="+3Hz">empathy without translation</prosody>: sharing the exact feeling of an emotion rather than trying to describe it in words. <break time="400ms"/> Or collaborative genius: where engineers, surgeons, and artists merge mental workspaces in real time!
    </mstts:express-as>
    <break time="700ms"/>

    <mstts:express-as style="cheerful" styledegree="1.2">
      Language was just our first operating system. <break time="350ms"/> <prosody pitch="+4Hz">The next OS will be direct neural resonance.</prosody>
    </mstts:express-as>
    <break time="600ms"/>

    <mstts:express-as style="friendly" styledegree="1.2">
      Thank you for joining today's journey into tomorrow on Future Human Daily. What thought would you share if words didn't exist? Connect with us, subscribe on Spotify or Apple Podcasts, and until tomorrow—stay curious about the future.
    </mstts:express-as>
  </voice>
</speak>"""

ssml_file = AUDIO_DIR / "ep-001-ssml.xml"
mp3_file = AUDIO_DIR / "ep-001.mp3"

with open(ssml_file, "w", encoding="utf-8") as f:
    f.write(ssml_content)

print("[Pro Audio Engine] Generating SSML Realistic Voiceover with Microsoft AndrewNeural...")

for attempt in range(5):
    try:
        cmd = [
            "edge-tts",
            "--file", str(ssml_file),
            "--write-media", str(mp3_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if mp3_file.exists() and mp3_file.stat().st_size > 1000:
            print(f"[Success] Generated realistic SSML ep-001.mp3 ({mp3_file.stat().st_size / 1024:.1f} KB)")
            break
        else:
            print(f"[Notice] Attempt {attempt+1} failed, retrying in 2s...")
    except Exception as e:
        print(f"[Notice] Retry {attempt+1}: {e}")

