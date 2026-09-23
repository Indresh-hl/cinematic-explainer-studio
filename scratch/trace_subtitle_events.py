import sys
sys.path.insert(0, ".")
import json
from script.render_full_master_video import build_adaptive_phrases

shots = json.load(open('assets/all_timeline_shots.json'))
data = json.load(open('assets/full_timeline_word_timestamps.json'))
phrases = build_adaptive_phrases(data)

target_w, target_h = 1934, 1080
fps = 30
total_duration = shots[-1]["end"]
total_frames = int(round(fps * total_duration))

# Let's trace what phrase and words are shown at each frame
active_shot_idx = 0
active_phrase_idx = 0

events = []
current_event = None

for frame_idx in range(total_frames):
    t = frame_idx / fps
    
    while active_shot_idx < len(shots) - 1 and t >= shots[active_shot_idx]["end"]:
        active_shot_idx += 1
    current_shot = shots[active_shot_idx]
    
    while active_phrase_idx < len(phrases) - 1 and t > phrases[active_phrase_idx]["end"]:
        active_phrase_idx += 1
    cur_p = phrases[active_phrase_idx]
    is_phrase_active = (cur_p["start"] <= t <= cur_p["end"])
    
    if is_phrase_active:
        state = (cur_p["text"], current_shot["name"])
    else:
        state = (None, current_shot["name"])
        
    if current_event is None or state != current_event["state"]:
        if current_event is not None:
            current_event["end_t"] = t
            events.append(current_event)
        current_event = {
            "state": state,
            "start_t": t,
            "end_t": t
        }

if current_event is not None:
    events.append(current_event)

print(f"Total subtitle display events: {len(events)}")

# Check if any phrase text appears more than once!
phrase_occurrences = {}
for e in events:
    txt = e["state"][0]
    if txt is not None:
        if txt not in phrase_occurrences:
            phrase_occurrences[txt] = []
        phrase_occurrences[txt].append(e)

for txt, occ_list in phrase_occurrences.items():
    if len(occ_list) > 1:
        # Check if the gap between them is small or if it's split across a shot
        print(f"\n[REPEATED SUBTITLE TEXT]: \"{txt}\"")
        for occ in occ_list:
            print(f"  Appeared at {occ['start_t']:.2f}s - {occ['end_t']:.2f}s on shot {occ['state'][1]}")
