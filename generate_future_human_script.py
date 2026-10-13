# =============================================================================
# FUTURE HUMAN DAILY: WEEKDAY SCRIPT WRITER (topic-ledger driven)
# Every weekday: pick the next topic that has NEVER aired -> write a fresh
# script with today's date -> validate -> record in future_human_history.json.
# Same-day reruns reuse the cached script (no double-booking of topics).
# =============================================================================

from datetime import datetime, timedelta

import future_human_ledger as L

SPEAKERS = {"Alex": "Puck", "Elena": "Kore"}
MIN_WORDS = 1300
MIN_TURNS = 20

SYSTEM_PROMPT = """You write scripts for "Future Human Daily", a daily 7-9 minute science & technology podcast hosted by Alex Mercer and Dr. Elena Vance.

HOSTS:
- Alex Mercer (speaker "Alex"): curious, relatable everyman. Asks the questions a smart listener on their morning commute would ask, pushes back with healthy skepticism, uses everyday analogies (traffic, coffee, phone batteries, kitchens, sports).
- Dr. Elena Vance (speaker "Elena"): brilliant physicist and biomedical engineer. Warm, passionate, precise. Explains mechanisms with vivid physical metaphors (water pipes, tuning forks, conveyor belts, locks and keys) and real numbers.

STYLE:
- Each turn starts with one emotion tag in square brackets, e.g. [warmly], [excitedly], [thoughtfully], [chuckles], [serious], [impressed], [cheerful]. No other bracketed text.
- 24 to 28 alternating turns, Alex first. Each turn 50-80 words. Total 1,400 to 1,700 words.
- Structure: (1) relatable everyday hook, (2) how it actually works, explained mechanically, (3) real-world applications and who benefits, (4) honest reality check: engineering bottlenecks, costs, risks, open questions, (5) realistic 5-10 year outlook, (6) sign-off.
- Be factually careful. Do not invent specific company announcements, study results, or statistics you are unsure of; describe the state of the field in general terms instead.
- Spell numbers the way they should be spoken.

HARD RULES:
- NEVER mention episode numbers of any kind.
- NEVER call this a first, inaugural, premiere, or launch episode. The show is ongoing.
- Do not reference other specific past episodes.

OUTPUT: strictly valid JSON:
{"title": "...", "summary": "1-2 sentence show-notes summary", "turns": [{"speaker": "Alex", "text": "..."}, {"speaker": "Elena", "text": "..."}]}
"""


def _sign_off_rule(date_obj):
    if date_obj.weekday() == 4:
        return ("This is the Friday show. In the final two turns, Alex thanks listeners for the week, reminds them to subscribe on "
                "Spotify and Apple Podcasts, says Veda and Rami host the Weekend Recap on Saturday and Sunday, and ends with 'Stay curious!'. "
                "Elena wishes everyone a restful weekend and says she and Alex are back Monday morning.")
    tomorrow = (date_obj + timedelta(days=1)).strftime("%A")
    return (f"In the final two turns, Alex thanks listeners for spending their {date_obj:%A} with the show, reminds them to subscribe on "
            f"Spotify and Apple Podcasts, and ends with 'Stay curious!'. Elena says goodbye and that they will be back tomorrow morning for {tomorrow}'s deep dive.")


def _user_prompt(topic, date_obj, recent_titles):
    said = L.spoken_date(date_obj)
    return f"""Write today's full episode.

TODAY: {said}
TOPIC: {topic['title']}
ANGLE: {topic.get('description', '')}

Turn 1 (Alex) must begin exactly: "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is {said}, and you're listening to Future Human Daily. Today we are diving into {topic['title']}..."
Turn 2 (Elena) greets Alex with "Happy {date_obj:%A}".
{_sign_off_rule(date_obj)}

Recently aired topics (do NOT re-cover these): {'; '.join(recent_titles)}
Return only the JSON object."""


def _fallback_fixed_script(topic, date_obj):
    """Only the never-aired Synthetic Biology script is eligible as an offline backup."""
    if topic["id"] != "synthetic-biology-logic-gates":
        return None
    from future_human_weekday_scripts import get_future_human_script_for_day
    title, summary, turns = get_future_human_script_for_day(2, L.spoken_date(date_obj))
    today, tomorrow = date_obj.strftime("%A"), (date_obj + timedelta(days=1)).strftime("%A")
    for t in turns:
        t["text"] = t["text"].replace("Thursday", "__TMR__").replace("Wednesday", today).replace("__TMR__", tomorrow)
    return title, summary, turns


def get_or_create_future_human_script(date_obj=None):
    """Returns (title, summary, turns) for today. Raises if no fresh script can be produced."""
    date_obj = date_obj or datetime.now()
    date_iso = date_obj.strftime("%Y-%m-%d")
    cache_file = L.cache_path("fhd_weekday", date_obj)

    cached = L.read_cache(cache_file)
    if cached:
        return cached

    history = L.load_history()
    existing = L.entry_for_date(date_iso, "weekday", history)
    if existing:
        raise RuntimeError(f"[LEDGER] {date_iso} already aired '{existing['title']}' but no cached script exists. "
                           f"Refusing to generate a second episode for the same day.")

    topic = L.next_unused_topic("weekday", history)
    if not topic:
        raise RuntimeError("[LEDGER] Topic backlog exhausted! Add new topics to future_human_topics.json.")
    print(f"[NEW TOPIC] {topic['title']} (id: {topic['id']}) | "
          f"{len(L.remaining_topics('weekday')) - 1} weekday topics left after today", flush=True)

    recent = [h["title"] for h in history[-15:]]
    said = L.spoken_date(date_obj)

    def validator(data):
        return L.validate_turns(data.get("turns"), set(SPEAKERS), SPEAKERS, said, MIN_WORDS, MIN_TURNS)

    data = L.generate_json_script(SYSTEM_PROMPT, _user_prompt(topic, date_obj, recent), validator)
    source = "generated"
    if data:
        title, summary, turns = topic["title"], data.get("summary") or topic.get("description", ""), data["turns"]
    else:
        # Safety net: the Synthetic Biology script was written but never aired. Use it once;
        # today's planned topic stays unused and becomes tomorrow's topic.
        backup_topic = next((t for t in L.load_topics() if t["id"] == "synthetic-biology-logic-gates"), None)
        fb = _fallback_fixed_script(backup_topic, date_obj) if backup_topic and not L.is_topic_used(backup_topic, history) else None
        if not fb:
            raise RuntimeError("[ABORT] Script generation failed on all models and no unused backup exists. "
                               "Not publishing rather than repeating an old episode.")
        topic = backup_topic
        title, summary, turns = fb
        source = "backup-fixed-script"
        print("[FALLBACK] Gemini unavailable; using never-aired backup script (Synthetic Biology).", flush=True)

    L.record_topic(date_iso, "weekday", topic["id"], title, summary, source)
    L.write_cache(cache_file, title, summary, turns)
    return title, summary, turns


if __name__ == "__main__":
    import sys
    d = datetime.strptime(sys.argv[1], "%Y-%m-%d") if len(sys.argv) > 1 else datetime.now()
    t, s, turns = get_or_create_future_human_script(d)
    print(f"\n{t}\n{s}\nTurns: {len(turns)} | Words: {sum(len(x['text'].split()) for x in turns)}")
