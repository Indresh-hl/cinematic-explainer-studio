import json

data = json.load(open('assets/full_timeline_word_timestamps.json'))
segs = data['segments']
for i in range(len(segs) - 1):
    if segs[i]['end'] > segs[i+1]['start']:
        print(f"Seg {i} end {segs[i]['end']} > Seg {i+1} start {segs[i+1]['start']}")
        print(f"  Seg {i}: \"{segs[i]['text']}\"")
        print(f"  Seg {i+1}: \"{segs[i+1]['text']}\"")
