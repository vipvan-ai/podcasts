# =============================================================================
# FUTURE HUMAN DAILY: WEEKEND SCRIPT WRITER (topic-ledger driven)
# Saturday : Veda & Rami recap THIS week's actual weekday episodes (from ledger)
# Sunday   : Veda & Rami "Sunday AI Catchup" on a never-aired AI topic
# =============================================================================

from datetime import datetime, timedelta

import future_human_ledger as L

SPEAKERS = {"Veda": "Veda", "Rami": "Rami"}
MIN_WORDS = 1300
MIN_TURNS = 20

SYSTEM_PROMPT = """You write the weekend edition of "Future Human Daily", a science & technology podcast. On weekends the weekday hosts (Alex Mercer and Dr. Elena Vance) are off, and two relaxed co-hosts take over:
- Veda (speaker "Veda"): upbeat, warm, playful, great at big-picture connections and "why this matters to you".
- Rami (speaker "Rami"): thoughtful, enthusiastic, loves the mechanics and the numbers, explains with everyday analogies.

STYLE:
- Relaxed weekend-coffee conversation, still substantive.
- Each turn starts with one emotion tag in square brackets, e.g. [upbeat], [warmly], [thoughtfully], [chuckles], [excitedly], [impressed]. No other bracketed text.
- 24 to 28 alternating turns, Veda first. Each turn 50-80 words. Total 1,400 to 1,700 words.
- Be factually careful; do not invent specific announcements, studies, or statistics you are unsure of.
- Spell numbers the way they should be spoken.

HARD RULES:
- NEVER mention episode numbers of any kind.
- NEVER call this a first, inaugural, premiere, or launch episode. The show is ongoing.

OUTPUT: strictly valid JSON:
{"title": "...", "summary": "1-2 sentence show-notes summary", "turns": [{"speaker": "Veda", "text": "..."}, {"speaker": "Rami", "text": "..."}]}
"""


def _week_topics(date_obj, history):
    start = (date_obj - timedelta(days=date_obj.weekday())).strftime("%Y-%m-%d")  # Monday
    end = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
    return [h for h in history if h.get("kind") == "weekday" and start <= h["date"] <= end]


def _saturday_prompt(date_obj, week):
    said = L.spoken_date(date_obj)
    lines = "\n".join(f"- {datetime.strptime(h['date'], '%Y-%m-%d'):%A}: {h['title']} -- {h.get('summary', '')}" for h in week)
    return f"""Write the SATURDAY WEEKEND RECAP.

TODAY: {said}
THIS WEEK'S EPISODES (Alex & Elena) to recap, in order:
{lines}

Turn 1 (Veda) must begin: "[upbeat] Happy Saturday, everyone! Welcome to the Future Human Daily Weekend Recap. Today is {said}. Alex Mercer and Dr. Elena Vance are taking their weekend break, so I am Veda with Rami..."
Walk through each of this week's topics above (give the most interesting two extra depth), connect them to each other and to everyday life, then pick a favorite takeaway each.
Final two turns: thank listeners, remind them to subscribe on Spotify and Apple Podcasts, and say Veda and Rami are back tomorrow for the Sunday AI Catchup.
The "title" must start with "Saturday Weekend Recap: " followed by a short phrase naming two of this week's topics.
Return only the JSON object."""


def _sunday_prompt(date_obj, topic, recent_titles):
    said = L.spoken_date(date_obj)
    return f"""Write the SUNDAY AI CATCHUP.

TODAY: {said}
TOPIC: {topic['title']}
ANGLE: {topic.get('description', '')}

Turn 1 (Veda) must begin: "[upbeat] Happy Sunday, everyone! Welcome to the Future Human Daily Sunday AI Catchup. Today is {said}. I am Veda with Rami, and today we are talking about {topic['title']}..."
Cover: an everyday hook, how it works, where it is already showing up, honest limitations and risks, and what to watch over the next few years.
Final two turns: thank listeners, remind them to subscribe on Spotify and Apple Podcasts, and say Alex Mercer and Dr. Elena Vance are back tomorrow morning with a brand-new weekday deep dive.
Recently aired topics (do NOT re-cover these): {'; '.join(recent_titles)}
Return only the JSON object."""


def get_or_create_weekend_script(date_obj=None, is_sunday=None):
    """Returns (title, summary, turns). Raises rather than repeating an old weekend script."""
    date_obj = date_obj or datetime.now()
    if is_sunday is None:
        is_sunday = date_obj.weekday() == 6
    kind = "sunday" if is_sunday else "saturday_recap"
    date_iso = date_obj.strftime("%Y-%m-%d")
    cache_file = L.cache_path(f"fhd_{kind}", date_obj)

    cached = L.read_cache(cache_file)
    if cached:
        return cached

    history = L.load_history()
    existing = L.entry_for_date(date_iso, kind, history)
    if existing:
        raise RuntimeError(f"[LEDGER] {date_iso} already aired '{existing['title']}' but no cached script exists. "
                           f"Refusing to generate a second {kind} episode for the same day.")

    said = L.spoken_date(date_obj)
    recent = [h["title"] for h in history[-15:]]

    def validator(data):
        return L.validate_turns(data.get("turns"), set(SPEAKERS), SPEAKERS, said, MIN_WORDS, MIN_TURNS)

    if is_sunday:
        topic = L.next_unused_topic("sunday", history)
        if not topic:
            raise RuntimeError("[LEDGER] Sunday topic backlog exhausted! Add 'sunday' topics to future_human_topics.json.")
        print(f"[NEW SUNDAY TOPIC] {topic['title']} (id: {topic['id']})", flush=True)
        data = L.generate_json_script(SYSTEM_PROMPT, _sunday_prompt(date_obj, topic, recent), validator)
        if not data:
            raise RuntimeError("[ABORT] Sunday script generation failed. Not publishing rather than repeating an old episode.")
        title = f"Sunday AI Catchup: {topic['title']}"
        topic_id = topic["id"]
    else:
        week = _week_topics(date_obj, history)
        if not week:
            raise RuntimeError("[ABORT] No weekday episodes recorded this week; nothing to recap.")
        print(f"[SATURDAY RECAP] Recapping {len(week)} episodes: {[h['title'] for h in week]}", flush=True)
        data = L.generate_json_script(SYSTEM_PROMPT, _saturday_prompt(date_obj, week), validator)
        if not data:
            raise RuntimeError("[ABORT] Saturday recap generation failed. Not publishing rather than repeating an old episode.")
        title = data.get("title") or ""
        if not title.startswith("Saturday Weekend Recap:"):
            title = f"Saturday Weekend Recap: {week[0]['title'].split('&')[0].strip()} & More"
        topic_id = f"saturday-recap-{date_obj:%Y%m%d}"

    summary = data.get("summary", "")
    turns = data["turns"]
    L.record_topic(date_iso, kind, topic_id, title, summary, "generated")
    L.write_cache(cache_file, title, summary, turns)
    return title, summary, turns


if __name__ == "__main__":
    import sys
    d = datetime.strptime(sys.argv[1], "%Y-%m-%d") if len(sys.argv) > 1 else datetime.now()
    t, s, turns = get_or_create_weekend_script(d)
    print(f"\n{t}\n{s}\nTurns: {len(turns)} | Words: {sum(len(x['text'].split()) for x in turns)}")
