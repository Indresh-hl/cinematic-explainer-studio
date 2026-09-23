import sys
sys.path.insert(0, ".")
import json
from script.render_full_master_video import build_adaptive_phrases

shots = json.load(open('assets/all_timeline_shots.json'))
data = json.load(open('assets/full_timeline_word_timestamps.json'))
phrases = build_adaptive_phrases(data)

# Let's inspect shots and phrases from 470s to 503.27s
print("=== SHOTS AND PHRASES FROM 480s TO 503s ===")
for s in shots:
    if s['end'] >= 480.0:
        print(f"\nSHOT: {s['name']} [{s['start']:.2f}s - {s['end']:.2f}s] (dur: {s['duration']:.2f}s)")
        # Find all phrases that fall inside or overlap with this shot
        for p in phrases:
            # Overlap condition
            if max(s['start'], p['start']) < min(s['end'], p['end']):
                overlap_start = max(s['start'], p['start'])
                overlap_end = min(s['end'], p['end'])
                print(f"   Phrase: \"{p['text']}\" [{p['start']:.2f}s - {p['end']:.2f}s] -> on shot for {overlap_end - overlap_start:.2f}s (from {overlap_start:.2f}s to {overlap_end:.2f}s)")
