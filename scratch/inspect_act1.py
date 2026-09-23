import json

with open("assets/full_timeline_word_timestamps.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("--- Act 1 Segments (0 to 75s) ---")
for s in data["segments"]:
    if s["start"] <= 75.0:
        print(f"[{s['start']:0.2f}s - {s['end']:0.2f}s] {s['text']}")
