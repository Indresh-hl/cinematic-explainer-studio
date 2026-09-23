import json

data = json.load(open('assets/full_timeline_word_timestamps.json'))
for s in data['segments'][:20]:
    print(f"[{s['id']:2d}] ({s['start']:5.1f}s - {s['end']:5.1f}s): {s['text']}")
