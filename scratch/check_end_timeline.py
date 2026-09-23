import sys
sys.path.insert(0, ".")
import json
from script.render_full_master_video import build_adaptive_phrases

shots = json.load(open('assets/all_timeline_shots.json'))
data = json.load(open('assets/full_timeline_word_timestamps.json'))
phrases = build_adaptive_phrases(data)

print("--- Shots from 475s to end ---")
for s in shots:
    if s['end'] >= 475.0:
        print(f"Shot {s['name']}: {s['start']:.2f}s -> {s['end']:.2f}s ({s['duration']:.2f}s)")

print("\n--- Phrases from 475s to end ---")
for p in phrases:
    if p['end'] >= 475.0:
        print(f"Phrase [{p['start']:.2f}s -> {p['end']:.2f}s]: \"{p['text']}\"")
