import sys
sys.path.insert(0, ".")
import json
import re

# Load script lines from teleprompter
with open("script/teleprompter_clean.txt", "r", encoding="utf-8") as f:
    raw_lines = f.readlines()

script_lines = []
for line in raw_lines:
    line = line.strip()
    if not line or line.startswith("=") or line.startswith("ISY") or line.startswith("TOPIC") or line.startswith("TOTAL") or line.startswith("PACING") or line.startswith("[PAUSE"):
        continue
    script_lines.append(line)

print(f"Total script lines: {len(script_lines)}")

# Load whisper segments
data = json.load(open("assets/full_timeline_word_timestamps.json", encoding="utf-8"))
whisper_segments = data["segments"]
print(f"Total whisper segments: {len(whisper_segments)}")

# Let's check for any repeated phrases or words across consecutive segments or phrases
from script.render_full_master_video import build_adaptive_phrases
phrases = build_adaptive_phrases(data)

# Let's inspect all phrases and see if any word or phrase is repeated within 10 seconds
for i in range(len(phrases)):
    p1 = phrases[i]
    words1 = [w['word'].strip().lower().strip(".,!?:;\"'-") for w in p1['words']]
    
    for j in range(i + 1, min(i + 8, len(phrases))):
        p2 = phrases[j]
        words2 = [w['word'].strip().lower().strip(".,!?:;\"'-") for w in p2['words']]
        
        # Check if identical phrase
        if words1 == words2:
            print(f"\n[EXACT DUPLICATE PHRASE]")
            print(f"  Phrase {i} at {p1['start']:.2f}s - {p1['end']:.2f}s: \"{p1['text']}\"")
            print(f"  Phrase {j} at {p2['start']:.2f}s - {p2['end']:.2f}s: \"{p2['text']}\"")
            
        # Check if 2 consecutive words match
        for k in range(len(words1) - 1):
            pair1 = (words1[k], words1[k+1])
            for m in range(len(words2) - 1):
                pair2 = (words2[m], words2[m+1])
                if pair1 == pair2 and p2['start'] - p1['start'] < 6.0:
                    print(f"\n[REPEATED WORD PAIR: {' '.join(pair1)}]")
                    print(f"  Phrase {i} at {p1['start']:.2f}s: \"{p1['text']}\"")
                    print(f"  Phrase {j} at {p2['start']:.2f}s: \"{p2['text']}\"")
