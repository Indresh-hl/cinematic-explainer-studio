import sys
sys.path.insert(0, ".")
import json
from script.render_full_master_video import build_adaptive_phrases

shots = json.load(open('assets/all_timeline_shots.json'))
data = json.load(open('assets/full_timeline_word_timestamps.json'))
phrases = build_adaptive_phrases(data)

print(f"Total shots: {len(shots)}")
print(f"Total phrases: {len(phrases)}")

bleed_issues = []

for s_idx in range(len(shots) - 1):
    cut_t = shots[s_idx]['end']
    
    # Check phrases around this cut
    for p_idx, p in enumerate(phrases):
        # Starts before cut, ends after cut
        if p['start'] < cut_t < p['end']:
            dur_before = cut_t - p['start']
            dur_after = p['end'] - cut_t
            bleed_issues.append({
                "type": "straddle",
                "cut_t": cut_t,
                "shot_before": shots[s_idx]['name'],
                "shot_after": shots[s_idx+1]['name'],
                "phrase_idx": p_idx,
                "phrase": p['text'],
                "dur_before": dur_before,
                "dur_after": dur_after
            })

print(f"\nTotal phrases straddling shot cuts: {len(bleed_issues)}")
for b in bleed_issues:
    # Especially if dur_before < 0.35s (it just flashes before the cut)
    # OR if dur_after < 0.20s (it just flashes after the cut)
    flag = ""
    if b['dur_before'] < 0.35:
        flag = "[FLASH BEFORE CUT -> SHOWS AGAIN ON NEXT SHOT!]"
    elif b['dur_after'] < 0.20:
        flag = "[FLASH AFTER CUT -> TAIL ON NEXT SHOT!]"
    print(f"At {b['cut_t']:6.2f}s ({b['shot_before']} -> {b['shot_after']}): \"{b['phrase']}\" (before: {b['dur_before']:.2f}s, after: {b['dur_after']:.2f}s) {flag}")
