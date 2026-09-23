import json
import re
from difflib import SequenceMatcher

# Load teleprompter text as a single cleaned stream of words
with open("script/teleprompter_clean.txt", "r", encoding="utf-8") as f:
    raw_lines = f.readlines()

tele_words = []
for line in raw_lines:
    line = line.strip()
    if not line or line.startswith("=") or line.startswith("ISY") or line.startswith("TOPIC") or line.startswith("TOTAL") or line.startswith("PACING") or line.startswith("[PAUSE"):
        continue
    words = re.findall(r"\b[\w']+\b", line)
    tele_words.extend([w.lower() for w in words])

print(f"Teleprompter total words: {len(tele_words)}")

# Load whisper words
data = json.load(open("assets/full_timeline_word_timestamps.json", encoding="utf-8"))
whisper_words = []
for s in data["segments"]:
    for w in s.get("words", []):
        clean = re.findall(r"\b[\w']+\b", w["word"])
        if clean:
            whisper_words.append((clean[0].lower(), w["start"], w["end"], w["word"]))

print(f"Whisper total words: {len(whisper_words)}")

# Compare sequences using difflib
sm = SequenceMatcher(None, [w[0] for w in whisper_words], tele_words)
opcodes = sm.get_opcodes()

for tag, i1, i2, j1, j2 in opcodes:
    if tag == 'insert':
        # words in teleprompter but missing in whisper
        print(f"\n[MISSING in whisper at {whisper_words[min(i1, len(whisper_words)-1)][1]:.1f}s]:")
        print(f"  Teleprompter has: {' '.join(tele_words[j1:j2])}")
    elif tag == 'delete':
        # words in whisper but NOT in teleprompter (Extra words / repetition!)
        print(f"\n[EXTRA in whisper at {whisper_words[i1][1]:.1f}s - {whisper_words[i2-1][2]:.1f}s]:")
        print(f"  Whisper extra: {' '.join([w[3] for w in whisper_words[i1:i2]])}")
    elif tag == 'replace':
        w_sub = [w[3] for w in whisper_words[i1:i2]]
        t_sub = tele_words[j1:j2]
        # Only print if not just minor punctuation/homophone
        if len(w_sub) != len(t_sub) or any(a.lower() != b.lower() for a, b in zip(w_sub, t_sub)):
            print(f"\n[DIFFERENCE at {whisper_words[i1][1]:.1f}s]:")
            print(f"  Whisper:      {' '.join(w_sub)}")
            print(f"  Teleprompter: {' '.join(t_sub)}")
