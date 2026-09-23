import sys
sys.path.insert(0, ".")
import json
from script.render_full_master_video import build_adaptive_phrases
data = json.load(open('assets/full_timeline_word_timestamps.json'))
phrases = build_adaptive_phrases(data)
for i in range(len(phrases)-1):
    if phrases[i]['start'] > phrases[i+1]['start']:
        print(f"Unsorted: phrase {i} ({phrases[i]['start']}) > phrase {i+1} ({phrases[i+1]['start']})")
print(f"Checked {len(phrases)} phrases.")
