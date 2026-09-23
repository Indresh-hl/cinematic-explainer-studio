import json

with open("assets/full_timeline_word_timestamps.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for seg in data["segments"][:6]:
    print(f"[{seg['start']:0.2f}s - {seg['end']:0.2f}s]: {seg['text']}")
    for w in seg["words"]:
        print(f"   {w['start']:0.2f}s - {w['end']:0.2f}s: '{w['word']}'")
