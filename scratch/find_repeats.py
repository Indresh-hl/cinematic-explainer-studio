import sys
sys.path.insert(0, ".")
import json

data = json.load(open('assets/full_timeline_word_timestamps.json'))
segments = data['segments']

print(f"Total segments: {len(segments)}")

all_words = []
for s_idx, s in enumerate(segments):
    for w in s.get('words', []):
        all_words.append((s_idx, w))

print(f"Total words: {len(all_words)}")

print("\n--- Duplicate words close in time (< 3.0s) ---")
for i in range(len(all_words) - 1):
    s1, w1 = all_words[i]
    s2, w2 = all_words[i+1]
    word1 = w1['word'].strip().lower().strip('.,!?-')
    word2 = w2['word'].strip().lower().strip('.,!?-')
    
    if word1 and word1 == word2 and abs(w1['start'] - w2['start']) < 3.0:
        print(f"Duplicate word '{word1}':")
        print(f"  [Seg {s1}] {w1}")
        print(f"  [Seg {s2}] {w2}")

print("\n--- Segment boundary phrase overlaps ---")
for i in range(len(segments) - 1):
    seg1 = segments[i]
    seg2 = segments[i+1]
    
    words1 = [w['word'].strip().lower().strip('.,!?-') for w in seg1.get('words', [])]
    words2 = [w['word'].strip().lower().strip('.,!?-') for w in seg2.get('words', [])]
    
    for k in range(1, min(len(words1), len(words2), 6)):
        if words1[-k:] == words2[:k]:
            print(f"\n[OVERLAP between Seg {i} and {i+1}]")
            print(f"  Seg {i} end ({seg1['end']}s): ... {' '.join(words1[-k:])}")
            print(f"  Seg {i+1} start ({seg2['start']}s): {' '.join(words2[:k])} ...")

from script.render_full_master_video import build_adaptive_phrases
phrases = build_adaptive_phrases(data)

print("\n--- Time overlaps between phrases ---")
overlaps = []
for i in range(len(phrases) - 1):
    p1 = phrases[i]
    p2 = phrases[i+1]
    if p2['start'] < p1['end']:
        overlaps.append((i, p1, p2))

print(f"Total phrase time overlaps: {len(overlaps)}")
for idx, p1, p2 in overlaps[:15]:
    diff = p1['end'] - p2['start']
    print(f"  Overlap {idx}: '{p1['text']}' ({p1['start']}s -> {p1['end']}s) overlaps '{p2['text']}' ({p2['start']}s -> {p2['end']}s) by {diff:.2f}s")
