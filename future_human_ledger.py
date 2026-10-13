# =============================================================================
# FUTURE HUMAN DAILY: TOPIC LEDGER
# - future_human_topics.json  : backlog of topics ready to be used
# - future_human_history.json : every topic that has ever aired (never reused)
# A topic is considered "used" if its id is in history OR its title overlaps
# heavily with any previously aired title (guards against re-worded repeats).
# =============================================================================

import os
import re
import json
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TOPICS_FILE = BASE_DIR / "future_human_topics.json"
HISTORY_FILE = BASE_DIR / "future_human_history.json"
SCRIPTS_CACHE_DIR = BASE_DIR / "future_human_scripts_cache"

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for _line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in _line and not _line.strip().startswith("#"):
            _k, _v = _line.strip().split("=", 1)
            os.environ.setdefault(_k, _v)

# Text models tried in order for script writing (gemini-2.5-* are retired for this key)
SCRIPT_MODELS = [
    "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash",
    "gemini-3.1-pro-preview", "gemini-pro-latest", "gemini-flash-latest",
    "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest", "gemma-4-31b-it",
]
GENERATION_ROUNDS = 5          # full passes over SCRIPT_MODELS
ROUND_BACKOFF_SECONDS = 120    # wait between passes (handles temporary 503 overloads)

_STOPWORDS = {
    "the", "and", "with", "from", "into", "that", "this", "your", "how", "what", "why",
    "future", "human", "daily", "science", "technology", "next", "generation", "new",
    "sunday", "saturday", "weekend", "recap", "catchup", "life", "after", "over", "about",
}

BANNED_PATTERNS = [
    r"\b(episode|ep)\s*(#|no\.?|number)?\s*\d+",
    r"\binaugural\b", r"\bpremiere\b", r"\blaunch week\b", r"\bfirst episode\b",
    r"\bdebut episode\b", r"\bvery first episode\b",
]


# ----------------------------------------------------------------------------- io
def _read_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise RuntimeError(f"[LEDGER] Could not parse {path.name}: {e}")
    return default


def load_topics():
    return _read_json(TOPICS_FILE, [])


def load_history():
    return _read_json(HISTORY_FILE, [])


def save_history(history):
    history = sorted(history, key=lambda h: (h.get("date", ""), h.get("kind", "")))
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------------ dedupe logic
def _keywords(title):
    title = re.sub(r"^(EP\s*\d+:|Sunday AI Catchup:|Saturday Weekend Recap:)\s*", "", title, flags=re.I)
    words = re.findall(r"[a-z]+", title.lower())
    out = set()
    for w in words:
        if len(w) < 4 or w in _STOPWORDS:
            continue
        if w.endswith("s") and len(w) > 4:
            w = w[:-1]
        out.add(w)
    return out


def is_topic_used(topic, history):
    """True if this topic (by id, or by title similarity) has ever aired."""
    used_ids = {h.get("topic_id") for h in history}
    if topic["id"] in used_ids:
        return True
    kw = _keywords(topic["title"])
    for h in history:
        if h.get("kind") == "saturday_recap":
            continue  # recaps intentionally reference the week's topics
        if len(kw & _keywords(h.get("title", ""))) >= 2:
            return True
    return False


def next_unused_topic(day_type, history=None, topics=None):
    history = load_history() if history is None else history
    topics = load_topics() if topics is None else topics
    for t in topics:
        if t.get("day_type", "weekday") == day_type and not is_topic_used(t, history):
            return t
    return None


def remaining_topics(day_type):
    history = load_history()
    return [t for t in load_topics() if t.get("day_type", "weekday") == day_type and not is_topic_used(t, history)]


def entry_for_date(date_iso, kind, history=None):
    history = load_history() if history is None else history
    return next((h for h in history if h.get("date") == date_iso and h.get("kind") == kind), None)


def record_topic(date_iso, kind, topic_id, title, summary, source):
    history = load_history()
    if entry_for_date(date_iso, kind, history):
        return
    if any(h.get("topic_id") == topic_id for h in history):
        raise RuntimeError(f"[LEDGER] Refusing to record duplicate topic_id '{topic_id}'.")
    history.append({
        "date": date_iso,
        "kind": kind,
        "topic_id": topic_id,
        "title": title,
        "summary": summary,
        "source": source,
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
    })
    save_history(history)
    print(f"[LEDGER] Recorded '{title}' ({kind}, {date_iso}) in future_human_history.json", flush=True)


# --------------------------------------------------------------- script helpers
def spoken_date(date_obj):
    """e.g. 'Wednesday, October 14, 2026' (no zero padding)."""
    return f"{date_obj:%A}, {date_obj:%B} {date_obj.day}, {date_obj.year}"


def validate_turns(turns, allowed_speakers, voice_map, date_phrase, min_words, min_turns):
    """Normalises voices and raises ValueError if the script breaks any rule."""
    if not isinstance(turns, list) or len(turns) < min_turns:
        raise ValueError(f"only {len(turns) if isinstance(turns, list) else 0} turns (min {min_turns})")
    for t in turns:
        if t.get("speaker") not in allowed_speakers or not str(t.get("text", "")).strip():
            raise ValueError(f"bad turn: {str(t)[:80]}")
        t["voice"] = voice_map[t["speaker"]]
    if len({t["speaker"] for t in turns}) < len(allowed_speakers):
        raise ValueError("not all hosts speak")
    words = sum(len(t["text"].split()) for t in turns)
    if words < min_words:
        raise ValueError(f"only {words} words (min {min_words})")
    if date_phrase.lower() not in turns[0]["text"].lower():
        raise ValueError(f"opening turn does not state today's date '{date_phrase}'")
    full = " ".join(t["text"] for t in turns)
    for pat in BANNED_PATTERNS:
        m = re.search(pat, full, flags=re.I)
        if m:
            raise ValueError(f"banned phrase found: '{m.group(0)}'")
    if re.search(r"\{[A-Z_]+\}|\[insert", full, flags=re.I):
        raise ValueError("unfilled placeholder found")
    return words


def generate_json_script(system_prompt, user_prompt, validator):
    """Tries each model; returns parsed+validated dict or None."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
    dead = set()
    for rnd in range(1, GENERATION_ROUNDS + 1):
        for model in SCRIPT_MODELS:
            if model in dead:
                continue
            try:
                print(f" -> [round {rnd}] Writing script with {model}...", flush=True)
                if model.startswith("gemma"):
                    resp = client.models.generate_content(
                        model=model,
                        contents=system_prompt + "\n\n" + user_prompt,
                        config=types.GenerateContentConfig(temperature=0.8),
                    )
                else:
                    resp = client.models.generate_content(
                        model=model,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            temperature=0.8,
                        ),
                    )
                text = resp.text.strip()
                m = re.search(r"\{.*\}", text, flags=re.S)
                data = json.loads(m.group(0) if m else text)
                words = validator(data)
                print(f"    [OK] {model}: {len(data['turns'])} turns, {words} words", flush=True)
                return data
            except Exception as e:
                msg = str(e)
                if "404" in msg or "NOT_FOUND" in msg:
                    dead.add(model)
                print(f"    [Rejected] {model}: {msg[:200]}", flush=True)
        if rnd < GENERATION_ROUNDS:
            print(f" -> All models failed this round; waiting {ROUND_BACKOFF_SECONDS}s before retrying...", flush=True)
            time.sleep(ROUND_BACKOFF_SECONDS)
    return None


def cache_path(prefix, date_obj):
    SCRIPTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return SCRIPTS_CACHE_DIR / f"{prefix}_{date_obj:%Y%m%d}.json"


def read_cache(path):
    if path.exists():
        try:
            c = json.loads(path.read_text(encoding="utf-8"))
            print(f"[SCRIPT CACHE HIT] {c['title']}", flush=True)
            return c["title"], c["summary"], c["turns"]
        except Exception:
            pass
    return None


def write_cache(path, title, summary, turns):
    path.write_text(json.dumps({"title": title, "summary": summary, "turns": turns}, indent=2, ensure_ascii=False), encoding="utf-8")
