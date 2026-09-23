import json
shots = json.load(open('assets/all_timeline_shots.json'))
print(f"Total shots: {len(shots)}")
for i in range(len(shots)):
    for j in range(i+1, min(i+10, len(shots))):
        if shots[i]['name'] == shots[j]['name']:
            print(f"Shot repeated: {shots[i]['name']} at {shots[i]['start']}s and {shots[j]['start']}s (gap: {shots[j]['start'] - shots[i]['end']}s)")
