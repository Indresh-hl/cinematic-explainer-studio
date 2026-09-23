import sys
sys.path.insert(0, ".")
import json
from script.render_full_master_video import build_adaptive_phrases

shots = json.load(open('assets/all_timeline_shots.json'))
data = json.load(open('assets/full_timeline_word_timestamps.json'))
phrases = build_adaptive_phrases(data)

cut_times = [s['end'] for s in shots[:-1]]

adjusted_count = 0
for p in phrases:
    # Check if p['start'] is within 0.35s before any cut
    for cut_t in cut_times:
        if 0 < (cut_t - p['start']) < 0.35:
            old_start = p['start']
            p['start'] = cut_t
            adjusted_count += 1
            print(f"[Snapped start to cut {cut_t:.2f}s] \"{p['text']}\" (was {old_start:.2f}s -> now {p['start']:.2f}s)")
            
        # Check if p['end'] is within 0.20s after any cut
        if 0 < (p['end'] - cut_t) < 0.20:
            old_end = p['end']
            p['end'] = cut_t
            adjusted_count += 1
            print(f"[Clamped end to cut {cut_t:.2f}s] \"{p['text']}\" (was {old_end:.2f}s -> now {p['end']:.2f}s)")

print(f"\nTotal phrase adjustments: {adjusted_count}")
