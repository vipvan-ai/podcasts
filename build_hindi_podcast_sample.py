import io
import time
import soundfile as sf
import librosa
import numpy as np
import scipy.signal as signal
from pathlib import Path
from gtts import gTTS

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# 45-Second Conversational Hindi Dialogue
# Topic: "क्या AI ग्लासेज स्मार्टफोन की जगह ले लेंगे?" (Will AI Smart Glasses Replace Smartphones?)
HINDI_SCRIPT = [
    {
        "speaker": "Rami",
        "gender": "male",
        "text": "नमस्ते दोस्तों! फ़्यूचर ह्यूमन डेली के इस ख़ास एपिसोड में आपका स्वागत है। ज़रा सोचिए, अगर आपकी जेब में रखा स्मार्टफ़ोन हमेशा के लिए ग़ायब हो जाए और उसकी जगह सिर्फ़ एक हल्का सा चश्मा आ जाए?"
    },
    {
        "speaker": "Veda",
        "gender": "female",
        "text": "बिल्कुल रामी! और सबसे दिलचस्प बात यह है कि आपको स्क्रीन पर उंगलियाँ चलाने की ज़रूरत ही नहीं होगी। आप किसी ऐतिहासिक इमारत या किसी पौधे को देखते हैं, और AI तुरंत उसका पूरा ब्योरा आपकी आँखों के सामने रख देता है!"
    },
    {
        "speaker": "Rami",
        "gender": "male",
        "text": "सुनने में तो यह बिल्कुल जादुई लगता है, वेदा! लेकिन असली पहेली यह है—क्या लोग दिनभर अपने चेहरे पर कैमरा और माइक पहनकर घूमने के लिए तैयार होंगे? हमारी प्राइवेसी और बातचीत का क्या होगा?"
    },
    {
        "speaker": "Veda",
        "gender": "female",
        "text": "यही तो इस क्रांति का सबसे बड़ा सवाल है, रामी! सुविधा जितनी जादुई लगती है, हमारी निजी ज़िंदगी पर उसकी क़ीमत भी उतनी ही बड़ी हो सकती है। तो चलिए, इस दिलचस्प बहस की गहराई में उतरते हैं!"
    }
]

def apply_proximity_warmth(audio_samples, sample_rate=24000):
    # Studio Proximity warmth boost at 140Hz for male host
    f0 = 140.0
    Q = 1.0
    gain_db = 3.5
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

def build_hindi_podcast_sample():
    print("==========================================================")
    print("Generating 45s Master Hindi Podcast Sample: Rami & Veda")
    print("Topic: Will AI Glasses Replace Smartphones?")
    print("==========================================================")

    target_sr = 24000
    combined_audio = []
    pause_samples = int(target_sr * 0.42)  # 420ms natural conversational pause

    # 80Hz High Pass Filter for broadcast cleanup
    b_hp, a_hp = signal.butter(2, 80 / (target_sr / 2), btype='high')

    for idx, turn in enumerate(HINDI_SCRIPT):
        speaker = turn["speaker"]
        gender = turn["gender"]
        text = turn["text"]
        
        print(f"\n[Turn {idx+1}/{len(HINDI_SCRIPT)}] Synthesizing {speaker} ({gender})...")
        
        tts = gTTS(text=text, lang='hi', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        raw_samples, sr = sf.read(fp)
        if sr != target_sr:
            raw_samples = librosa.resample(raw_samples, orig_sr=sr, target_sr=target_sr)
            sr = target_sr

        # Host voice character modeling
        if gender == "male":
            # Pitch shift -3.5 semitones for Rami (warm male broadcast baritone)
            processed = librosa.effects.pitch_shift(raw_samples, sr=sr, n_steps=-3.5)
            processed = apply_proximity_warmth(processed, sr)
        else:
            # Subtle +0.4 semitone pitch boost for Veda (articulate female host)
            processed = librosa.effects.pitch_shift(raw_samples, sr=sr, n_steps=0.4)

        # 80Hz HPF & DC offset removal
        processed = signal.filtfilt(b_hp, a_hp, processed)
        processed -= np.mean(processed)

        # 20ms Cosine Fade-in / Fade-out
        fade_len = int(sr * 0.02)
        if len(processed) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            processed[:fade_len] *= fade_in
            processed[-fade_len:] *= fade_out

        combined_audio.append(processed)
        if idx < len(HINDI_SCRIPT) - 1:
            combined_audio.append(np.zeros(pause_samples, dtype=np.float32))

        print(f" -> Turn {idx+1} completed ({len(processed)/sr:.2f}s)")
        time.sleep(0.5)

    full_mix = np.concatenate(combined_audio)

    # Master broadcast peak normalization (-1.0 dBFS)
    max_peak = np.max(np.abs(full_mix))
    if max_peak > 0:
        full_mix = full_mix * (0.891 / max_peak)

    output_path = AUDIO_DIR / "sample_hindi_podcast_45s.mp3"
    sf.write(str(output_path), full_mix, target_sr)

    duration = len(full_mix) / target_sr
    print("\n==========================================================")
    print(f" [SUCCESS] Master Hindi Podcast Audio Created!")
    print(f" File: {output_path}")
    print(f" Total Duration: {duration:.2f} seconds")
    print("==========================================================")
    return output_path, duration

if __name__ == "__main__":
    build_hindi_podcast_sample()
