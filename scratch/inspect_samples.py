import sys
sys.path.insert(0, ".")
import json
from script.render_full_master_video import build_adaptive_phrases

shots = json.load(open('assets/all_timeline_shots.json'))
data = json.load(open('assets/full_timeline_word_timestamps.json'))
phrases = build_adaptive_phrases(data)

check_times = [4.5, 38.0, 115.0, 210.0, 320.0, 410.0, 485.0]

for t in check_times:
    s_name = 'Unknown'
    for s in shots:
        if s['start'] <= t < s['end']:
            s_name = s['name']
            break
            
    p_text = 'No phrase'
    for p in phrases:
        if p['start'] <= t <= p['end']:
            p_text = p['text']
            break
            
    print(f'Time {t:5.1f}s | Shot: {s_name:<10} | Active Text: "{p_text}"')
