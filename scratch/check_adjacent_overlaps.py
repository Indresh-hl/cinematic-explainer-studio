import sys
sys.path.insert(0, ".")
import json
from script.render_full_master_video import build_adaptive_phrases

data = json.load(open("assets/full_timeline_word_timestamps.json"))
phrases = build_adaptive_phrases(data)

print(f"Total phrases: {len(phrases)}")

# Let's inspect every single phrase and check its words
for i in range(len(phrases)):
    p = phrases[i]
    words = [w['word'] for w in p['words']]
    # check if any adjacent phrases have repeated words
    if i < len(phrases) - 1:
        next_p = phrases[i+1]
        next_words = [w['word'] for w in next_p['words']]
        
        # Check overlap
        for w in words:
            clean_w = w.lower().strip(".,!?:;\"'-")
            for nw in next_words:
                clean_nw = nw.lower().strip(".,!?:;\"'-")
                if clean_w and clean_w == clean_nw and len(clean_w) > 2:
                    print(f"[{i} -> {i+1}] ({p['start']:.1f}s -> {next_p['start']:.1f}s): word '{clean_w}' in both:")
                    print(f"   p{i}: \"{p['text']}\"")
                    print(f"   p{i+1}: \"{next_p['text']}\"")
