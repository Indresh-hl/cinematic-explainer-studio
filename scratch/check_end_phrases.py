import sys
sys.path.insert(0, ".")
import json
from script.render_full_master_video import build_adaptive_phrases

data = json.load(open('assets/full_timeline_word_timestamps.json'))
phrases = build_adaptive_phrases(data)

print("--- Phrases from 350s to 503s ---")
for idx, p in enumerate(phrases):
    if p['start'] >= 350.0:
        words_detail = " ".join([f"{w['word']}({w['start']:.2f}-{w['end']:.2f})" for w in p['words']])
        print(f"{idx:3d}: [{p['start']:6.2f}s - {p['end']:6.2f}s] \"{p['text']}\" -> {words_detail}")
